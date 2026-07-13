import asyncio

import pytest

from api.services.admin_menu_service import AdminMenuService
from api.services.menu_service import (
    MENU_CACHE_DIRTY_KEY,
    MenuCache,
    MenuItemRecord,
    MenuService,
    invalidate_menu_cache_after_commit,
    menu_cache,
)


def make_record(item_id: int = 1) -> MenuItemRecord:
    return MenuItemRecord(
        id=item_id,
        external_id=f"C{item_id:03d}",
        category_id=10,
        category_slug="sushi",
        category_name="Sushi",
        category_display_order=1,
        name="Salmon Roll",
        description="salmon",
        price=9.5,
        tags=["fresh"],
        is_available=True,
        display_order=1,
        language_code="en",
        allergens=["fish"],
    )


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_menu_cache_returns_stored_items_within_ttl() -> None:
    clock = FakeClock()
    cache = MenuCache(clock=clock)
    items = [make_record()]

    cache.store("en", items, ttl_seconds=60.0)
    clock.now = 59.0

    assert cache.get("en", ttl_seconds=60.0) is items


def test_menu_cache_expires_after_ttl() -> None:
    clock = FakeClock()
    cache = MenuCache(clock=clock)
    cache.store("en", [make_record()], ttl_seconds=60.0)
    clock.now = 61.0

    assert cache.get("en", ttl_seconds=60.0) is None


def test_menu_cache_disabled_when_ttl_is_zero() -> None:
    cache = MenuCache(clock=FakeClock())
    cache.store("en", [make_record()], ttl_seconds=0)

    assert cache.get("en", ttl_seconds=60.0) is None


def test_menu_cache_is_per_language() -> None:
    cache = MenuCache(clock=FakeClock())
    cache.store("en", [make_record()], ttl_seconds=60.0)

    assert cache.get("el", ttl_seconds=60.0) is None


def test_menu_cache_invalidate_clears_all_languages() -> None:
    cache = MenuCache(clock=FakeClock())
    cache.store("en", [make_record()], ttl_seconds=60.0)
    cache.store("el", [make_record()], ttl_seconds=60.0)
    cache.invalidate()

    assert cache.get("en", ttl_seconds=60.0) is None
    assert cache.get("el", ttl_seconds=60.0) is None


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def mappings(self):
        return self

    def all(self) -> list[dict]:
        return self._rows

    def one(self) -> dict:
        return self._rows[0]

    def one_or_none(self) -> dict | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.execute_calls = 0
        self.info: dict = {}

    async def execute(self, statement, params=None) -> FakeResult:
        self.execute_calls += 1
        return FakeResult(self.rows)


MENU_ROW = {
    "id": 1,
    "external_id": "C001",
    "category_id": 10,
    "category_slug": "sushi",
    "category_name": "Sushi",
    "category_display_order": 1,
    "name": "Salmon Roll",
    "description": "salmon",
    "price": 9.5,
    "tags": ["fresh"],
    "allergens": ["fish"],
    "is_available": True,
    "display_order": 1,
    "language_code": "en",
}


@pytest.mark.asyncio
async def test_fetch_items_hits_database_once_within_ttl() -> None:
    session = FakeSession([MENU_ROW])
    service = MenuService(session=session)

    first = await service.fetch_items(language_code="en")
    second = await service.fetch_items(language_code="en")

    assert session.execute_calls == 1
    assert first is second
    assert first[0].name == "Salmon Roll"


@pytest.mark.asyncio
async def test_admin_item_update_invalidates_menu_cache_after_commit() -> None:
    menu_session = FakeSession([MENU_ROW])
    menu_service = MenuService(session=menu_session)
    await menu_service.fetch_items(language_code="en")
    assert menu_cache.get("en", ttl_seconds=60.0) is not None

    admin_row = {
        "id": 1,
        "external_id": "C001",
        "category_id": 10,
        "name": "Salmon Roll",
        "description": "salmon",
        "price": 10.5,
        "tags": ["fresh"],
        "allergens": ["fish"],
        "is_available": True,
        "display_order": 1,
    }
    from api.schemas.admin_menu import MenuItemUpdateRequest

    admin_session = FakeSession([admin_row])
    admin_service = AdminMenuService(session=admin_session)
    await admin_service.update_item(1, MenuItemUpdateRequest(price=10.5))

    # Πριν το commit το cache μένει άθικτο (μόνο σημαδεμένο το session)...
    assert admin_session.info[MENU_CACHE_DIRTY_KEY] is True
    assert menu_cache.get("en", ttl_seconds=60.0) is not None

    # ...και ακυρώνεται μόλις το commit ολοκληρωθεί (after_commit listener).
    invalidate_menu_cache_after_commit(admin_session)
    assert menu_cache.get("en", ttl_seconds=60.0) is None


class SlowSession(FakeSession):
    """FakeSession που αργεί, ώστε όλα τα tasks να προλάβουν το miss path."""

    async def execute(self, statement, params=None) -> FakeResult:
        self.execute_calls += 1
        await asyncio.sleep(0.02)
        return FakeResult(self.rows)


@pytest.mark.asyncio
async def test_concurrent_cold_cache_fetches_run_a_single_query() -> None:
    """Anti-stampede: σε TTL expiry με N ταυτόχρονα requests, 1 query."""
    session = SlowSession([MENU_ROW])
    service = MenuService(session=session)

    results = await asyncio.gather(
        *(service.fetch_items(language_code="en") for _ in range(8))
    )

    assert session.execute_calls == 1
    assert all(result == results[0] for result in results)
