import pytest
from pydantic import ValidationError

from api.schemas.allergy import AllergyProfileUpsertRequest


def test_upsert_request_normalizes_allergens() -> None:
    request = AllergyProfileUpsertRequest(
        device_id="device-12345",
        allergens=["FISH", "gluten", "fish"],
    )

    assert request.allergens == ["gluten", "fish"]


def test_upsert_request_accepts_empty_list_to_clear_profile() -> None:
    request = AllergyProfileUpsertRequest(device_id="device-12345", allergens=[])

    assert request.allergens == []


def test_upsert_request_rejects_unknown_allergen() -> None:
    with pytest.raises(ValidationError):
        AllergyProfileUpsertRequest(device_id="device-12345", allergens=["pollen"])


def test_upsert_request_rejects_blank_device_id() -> None:
    with pytest.raises(ValidationError):
        AllergyProfileUpsertRequest(device_id="        ", allergens=["fish"])


def test_upsert_request_rejects_short_device_id() -> None:
    with pytest.raises(ValidationError):
        AllergyProfileUpsertRequest(device_id="short", allergens=["fish"])
