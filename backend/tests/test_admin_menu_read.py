from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_admin_menu_service, verify_internal_api_key
from api.main import app
from api.schemas.admin_menu import (
    MenuCategoryAdminDetailResponse,
    MenuCategoryListResponse,
    MenuItemAdminDetailResponse,
    MenuItemListResponse,
)
from api.services.admin_menu_service import AdminMenuService, decode_jsonb_object


def item_row(**overrides) -> dict:
    row = {
        "id": 7,
        "external_id": "m7",
        "category_id": 3,
        "category_name": "Σούσι",
        "name": "Σασίμι σολομού",
        "description": "Φρέσκος σολομός",
        "price": Decimal("12.50"),
        "tags": ["raw", "fish"],
        "is_available": True,
        "display_order": 2,
        "translations": {"en": {"name": "Salmon sashimi", "description": "Fresh salmon"}},
    }
    row.update(overrides)
    return row


def category_row(**overrides) -> dict:
    row = {
        "id": 3,
        "name": "Σούσι",
        "slug": "sushi",
        "display_order": 1,
        "item_count": 12,
        "translations": {"en": "Sushi", "de": "Sushi"},
    }
    row.update(overrides)
    return row


def test_decode_jsonb_object_returns_empty_dict_for_null_aggregate() -> None:
    assert decode_jsonb_object(None) == {}


def test_decode_jsonb_object_parses_raw_json_string() -> None:
    assert decode_jsonb_object('{"en": "Sushi"}') == {"en": "Sushi"}


def test_decode_jsonb_object_rejects_non_object_payloads() -> None:
    assert decode_jsonb_object("[1, 2]") == {}
    assert decode_jsonb_object("not json") == {}
    assert decode_jsonb_object(42) == {}


def test_item_detail_response_exposes_price_as_float_and_typed_translations() -> None:
    response = AdminMenuService._item_detail_response(item_row())

    assert response.price == 12.5
    assert response.tags == ["raw", "fish"]
    assert response.category_name == "Σούσι"
    assert response.translations["en"].name == "Salmon sashimi"
    assert response.translations["en"].description == "Fresh salmon"


def test_item_detail_response_defaults_missing_translation_fields() -> None:
    response = AdminMenuService._item_detail_response(
        item_row(translations={"de": {"name": "Lachs-Sashimi"}})
    )

    assert response.translations["de"].description == ""


def test_item_detail_response_drops_malformed_translation_entries() -> None:
    response = AdminMenuService._item_detail_response(
        item_row(translations={"en": "Salmon sashimi", "de": {"name": "Lachs", "description": ""}})
    )

    assert set(response.translations) == {"de"}


def test_item_detail_response_handles_items_without_translations() -> None:
    response = AdminMenuService._item_detail_response(item_row(translations=None, tags=None))

    assert response.translations == {}
    assert response.tags == []


def test_category_detail_response_carries_item_count_and_translations() -> None:
    response = AdminMenuService._category_detail_response(category_row())

    assert response.item_count == 12
    assert response.translations == {"en": "Sushi", "de": "Sushi"}


class FakeAdminMenuService:
    """Records the arguments the routes pass down, so filters can be asserted."""

    def __init__(self) -> None:
        self.list_items_calls: list[dict] = []
        self.deleted_items: list[int] = []
        self.deleted_categories: list[int] = []
        self.reordered: list[list[int]] = []
        self.missing_item_ids: set[int] = set()
        self.category_delete_error: Exception | None = None

    async def list_items(self, category_id=None, is_available=None, search=None) -> MenuItemListResponse:
        self.list_items_calls.append(
            {"category_id": category_id, "is_available": is_available, "search": search}
        )
        return MenuItemListResponse(total=1, items=[MenuItemAdminDetailResponse(**item_row(price=12.5))])

    async def get_item(self, item_id: int) -> MenuItemAdminDetailResponse:
        if item_id in self.missing_item_ids:
            raise LookupError(f"Menu item not found: {item_id}")
        return MenuItemAdminDetailResponse(**item_row(id=item_id, price=12.5))

    async def list_categories(self) -> MenuCategoryListResponse:
        return MenuCategoryListResponse(
            total=1,
            categories=[MenuCategoryAdminDetailResponse(**category_row())],
        )

    async def delete_item(self, item_id: int) -> None:
        if item_id in self.missing_item_ids:
            raise LookupError(f"Menu item not found: {item_id}")
        self.deleted_items.append(item_id)

    async def delete_category(self, category_id: int) -> None:
        if self.category_delete_error is not None:
            raise self.category_delete_error
        self.deleted_categories.append(category_id)

    async def reorder_items(self, item_ids: list[int]) -> int:
        self.reordered.append(item_ids)
        return len(item_ids)

    async def reorder_categories(self, category_ids: list[int]) -> int:
        self.reordered.append(category_ids)
        return len(category_ids)


def admin_client(service: FakeAdminMenuService) -> TestClient:
    app.dependency_overrides[get_admin_menu_service] = lambda: service
    app.dependency_overrides[verify_internal_api_key] = lambda: "test-key"
    return TestClient(app)


def test_admin_endpoints_reject_requests_without_an_api_key() -> None:
    with TestClient(app) as client:
        response = client.get("/api/admin/menu/items")

    assert response.status_code == 403


def test_list_items_passes_filters_to_the_service() -> None:
    service = FakeAdminMenuService()
    try:
        with admin_client(service) as client:
            response = client.get(
                "/api/admin/menu/items",
                params={"category_id": 3, "is_available": "false", "search": "σολομ"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert service.list_items_calls == [{"category_id": 3, "is_available": False, "search": "σολομ"}]


def test_list_items_without_filters_passes_none() -> None:
    service = FakeAdminMenuService()
    try:
        with admin_client(service) as client:
            response = client.get("/api/admin/menu/items")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.list_items_calls == [{"category_id": None, "is_available": None, "search": None}]


def test_get_item_returns_404_for_a_missing_item() -> None:
    service = FakeAdminMenuService()
    service.missing_item_ids = {99}
    try:
        with admin_client(service) as client:
            response = client.get("/api/admin/menu/items/99")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_delete_item_returns_204_and_404_for_a_missing_item() -> None:
    service = FakeAdminMenuService()
    service.missing_item_ids = {99}
    try:
        with admin_client(service) as client:
            deleted = client.delete("/api/admin/menu/items/7")
            missing = client.delete("/api/admin/menu/items/99")
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert missing.status_code == 404
    assert service.deleted_items == [7]


def test_delete_category_returns_409_when_it_still_has_items() -> None:
    service = FakeAdminMenuService()
    service.category_delete_error = IntegrityError("delete", {}, Exception("restrict"))
    try:
        with admin_client(service) as client:
            response = client.delete("/api/admin/menu/categories/3")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_reorder_items_returns_the_updated_count() -> None:
    service = FakeAdminMenuService()
    try:
        with admin_client(service) as client:
            response = client.put("/api/admin/menu/items/reorder", json={"ids": [3, 1, 2]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"updated": 3}
    assert service.reordered == [[3, 1, 2]]


def test_reorder_rejects_duplicate_ids() -> None:
    service = FakeAdminMenuService()
    try:
        with admin_client(service) as client:
            response = client.put("/api/admin/menu/items/reorder", json={"ids": [1, 1]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert service.reordered == []


def test_reorder_route_is_not_shadowed_by_the_item_id_route() -> None:
    service = FakeAdminMenuService()
    try:
        with admin_client(service) as client:
            response = client.put("/api/admin/menu/categories/reorder", json={"ids": [2, 1]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.reordered == [[2, 1]]
