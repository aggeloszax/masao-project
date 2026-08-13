from api.main import app
from api.schemas.chat import MenuItemResponse
from api.schemas.menu import MenuItemPublicResponse


def test_removed_profile_routes_are_not_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/allergens" not in paths
    assert "/api/profile/allergies" not in paths


def test_public_menu_items_do_not_expose_retired_allergy_fields() -> None:
    fields = MenuItemPublicResponse.model_fields

    assert "allergens" not in fields
    assert "matched_allergens" not in fields
    assert "allergen_alert" not in fields


def test_chat_recommendations_do_not_expose_retired_allergy_fields() -> None:
    fields = MenuItemResponse.model_fields

    assert "allergens" not in fields
    assert "matched_allergens" not in fields
    assert "allergen_alert" not in fields
