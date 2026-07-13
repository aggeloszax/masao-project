import pytest
from sqlalchemy.exc import OperationalError

from api.services.allergy_service import (
    PROFILE_CACHE_DIRTY_KEY,
    AllergyService,
    invalidate_profile_cache_after_commit,
)


class FailingSession:
    """Session stub: κάθε query αποτυγχάνει (π.χ. πίνακας δεν υπάρχει)."""

    def __init__(self) -> None:
        self.info: dict = {}

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, statement, params=None):
        raise OperationalError("select 1", {}, Exception("relation does not exist"))


@pytest.mark.asyncio
async def test_try_get_customer_allergens_fails_open_on_db_error() -> None:
    service = AllergyService(session=FailingSession())

    allergens = await service.try_get_customer_allergens("device-12345")

    assert allergens == set()


@pytest.mark.asyncio
async def test_get_customer_allergens_propagates_db_error() -> None:
    service = AllergyService(session=FailingSession())

    with pytest.raises(OperationalError):
        await service.get_customer_allergens("device-12345")


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


class RecordingSession:
    """Session stub: μετρά τα queries και υποστηρίζει SAVEPOINT context."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.execute_calls = 0
        self.info: dict = {}

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, statement, params=None) -> FakeResult:
        self.execute_calls += 1
        return FakeResult(self.rows)


PROFILE_ROW = {"device_id": "device-12345", "allergens": ["milk"], "updated_at": None}
UPDATED_ROW = {"device_id": "device-12345", "allergens": ["eggs", "milk"], "updated_at": None}


@pytest.mark.asyncio
async def test_try_get_customer_allergens_uses_cache_within_ttl() -> None:
    session = RecordingSession([PROFILE_ROW])
    service = AllergyService(session=session)

    first = await service.try_get_customer_allergens("device-12345")
    second = await service.try_get_customer_allergens("device-12345")

    assert session.execute_calls == 1
    assert first == second == {"milk"}


@pytest.mark.asyncio
async def test_try_get_customer_allergens_caches_empty_profiles() -> None:
    session = RecordingSession([])  # καμία εγγραφή προφίλ για τη συσκευή
    service = AllergyService(session=session)

    first = await service.try_get_customer_allergens("device-12345")
    second = await service.try_get_customer_allergens("device-12345")

    # Το κενό προφίλ είναι κανονικό cache hit (negative caching) — 1 query.
    assert session.execute_calls == 1
    assert first == second == set()


@pytest.mark.asyncio
async def test_failed_lookup_is_not_cached() -> None:
    failing = AllergyService(session=FailingSession())
    assert await failing.try_get_customer_allergens("device-12345") == set()

    healthy = AllergyService(session=RecordingSession([PROFILE_ROW]))
    assert await healthy.try_get_customer_allergens("device-12345") == {"milk"}


@pytest.mark.asyncio
async def test_upsert_invalidates_cache_only_after_commit() -> None:
    read_session = RecordingSession([PROFILE_ROW])
    reader = AllergyService(session=read_session)
    await reader.try_get_customer_allergens("device-12345")

    write_session = RecordingSession([UPDATED_ROW])
    writer = AllergyService(session=write_session)
    await writer.upsert_profile("device-12345", ["eggs", "milk"])

    # Πριν το commit: το session είναι απλώς σημαδεμένο, το cache άθικτο.
    assert write_session.info[PROFILE_CACHE_DIRTY_KEY] == {"device-12345"}
    stale = await reader.try_get_customer_allergens("device-12345")
    assert stale == {"milk"}
    assert read_session.execute_calls == 1

    # Μετά το commit (after_commit listener): το επόμενο read ξαναπάει στη βάση.
    invalidate_profile_cache_after_commit(write_session)
    read_session.rows = [UPDATED_ROW]
    fresh = await reader.try_get_customer_allergens("device-12345")
    assert fresh == {"eggs", "milk"}
    assert read_session.execute_calls == 2
