import pytest
from pydantic import ValidationError

from api.schemas.admin_menu import (
    MenuCategoryUpdateRequest,
    MenuItemCreateRequest,
    MenuItemTranslationUpsertRequest,
    MenuItemUpdateRequest,
    patch_payload,
)


def test_item_update_accepts_availability_only_false() -> None:
    request = MenuItemUpdateRequest(is_available=False)

    assert patch_payload(request) == {"is_available": False}


def test_item_update_rejects_empty_patch() -> None:
    with pytest.raises(ValidationError):
        MenuItemUpdateRequest()


def test_category_update_rejects_empty_patch() -> None:
    with pytest.raises(ValidationError):
        MenuCategoryUpdateRequest()


def test_item_create_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        MenuItemCreateRequest(
            category_id=1,
            name="Test Roll",
            price=-1,
        )


def test_item_create_normalizes_tags() -> None:
    request = MenuItemCreateRequest(
        category_id=1,
        name="Test Roll",
        price=9.5,
        tags=[" spicy ", "spicy", "", " vegan "],
    )

    assert request.tags == ["spicy", "vegan"]


def test_item_translation_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        MenuItemTranslationUpsertRequest(name="   ", description="valid")


def test_item_create_normalizes_allergens() -> None:
    request = MenuItemCreateRequest(
        category_id=1,
        name="Test Roll",
        price=9.5,
        allergens=["FISH", "gluten", "fish"],
    )

    assert request.allergens == ["gluten", "fish"]


def test_item_create_rejects_unknown_allergen() -> None:
    with pytest.raises(ValidationError):
        MenuItemCreateRequest(
            category_id=1,
            name="Test Roll",
            price=9.5,
            allergens=["pollen"],
        )


def test_item_update_accepts_allergens_patch() -> None:
    request = MenuItemUpdateRequest(allergens=["fish"])

    assert patch_payload(request) == {"allergens": ["fish"]}
