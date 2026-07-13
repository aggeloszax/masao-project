"""Το /api/menu?device_id= δεν πρέπει να περιμένει το single-flight lock
κρατώντας σύνδεση από το προηγηθέν profile lookup (pool starvation)."""

import pytest

from api.routers.menu import menu
from api.services.allergy_service import AllergyService
from api.services.menu_service import MenuService

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


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def one(self):
        return self._rows[0]

    def one_or_none(self):
        return self._rows[0] if self._rows else None


class OrderRecordingSession:
    """Καταγράφει τη σειρά menu/profile queries για τον έλεγχο ordering."""

    def __init__(self):
        self.calls: list[str] = []
        self.info: dict = {}

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        if "from menu_items" in sql:
            self.calls.append("menu-select")
            return FakeResult([MENU_ROW])
        if "from customer_allergy_profiles" in sql:
            self.calls.append("profile-select")
            return FakeResult([])
        raise AssertionError(f"unexpected SQL: {sql}")


@pytest.mark.asyncio
async def test_menu_with_device_id_warms_menu_cache_before_profile_lookup() -> None:
    session = OrderRecordingSession()

    response = await menu(
        restaurant_slug="masao",
        language_code="en",
        include_unavailable=False,
        device_id="device-12345",
        service=MenuService(session=session),
        allergy_service=AllergyService(session=session),
    )

    # Το μενού πρώτα (χωρίς να κρατάμε σύνδεση στην αναμονή του lock),
    # μετά το προφίλ.
    assert session.calls.index("menu-select") < session.calls.index("profile-select")
    assert response.total_items == 1
