from datetime import UTC, datetime

from fastapi.testclient import TestClient

from api.dependencies import get_allergy_service
from api.main import app
from api.schemas.allergy import AllergyProfileResponse


class FakeAllergyService:
    def __init__(self) -> None:
        self.profiles: dict[str, list[str]] = {}

    async def get_profile(self, device_id: str) -> AllergyProfileResponse:
        return AllergyProfileResponse(
            device_id=device_id,
            allergens=self.profiles.get(device_id, []),
            updated_at=datetime.now(UTC) if device_id in self.profiles else None,
        )

    async def upsert_profile(self, device_id: str, allergens: list[str]) -> AllergyProfileResponse:
        self.profiles[device_id] = allergens
        return AllergyProfileResponse(
            device_id=device_id,
            allergens=allergens,
            updated_at=datetime.now(UTC),
        )


def test_allergen_catalogue_returns_14_localized_options() -> None:
    with TestClient(app) as client:
        response = client.get("/api/allergens", params={"language_code": "en"})

    assert response.status_code == 200
    body = response.json()
    assert body["language_code"] == "en"
    assert len(body["allergens"]) == 14
    codes = [option["code"] for option in body["allergens"]]
    assert "fish" in codes
    fish = next(option for option in body["allergens"] if option["code"] == "fish")
    assert fish["label"] == "Fish"


def test_allergy_profile_upsert_and_read_roundtrip() -> None:
    fake = FakeAllergyService()
    app.dependency_overrides[get_allergy_service] = lambda: fake

    try:
        with TestClient(app) as client:
            put_response = client.put(
                "/api/profile/allergies",
                json={"device_id": "device-12345", "allergens": ["fish", "FISH", "sesame"]},
            )
            get_response = client.get(
                "/api/profile/allergies",
                params={"device_id": "device-12345"},
            )

        assert put_response.status_code == 200
        assert put_response.json()["allergens"] == ["fish", "sesame"]
        assert get_response.status_code == 200
        assert get_response.json()["allergens"] == ["fish", "sesame"]
    finally:
        app.dependency_overrides.clear()


def test_allergy_profile_upsert_rejects_unknown_codes() -> None:
    fake = FakeAllergyService()
    app.dependency_overrides[get_allergy_service] = lambda: fake

    try:
        with TestClient(app) as client:
            response = client.put(
                "/api/profile/allergies",
                json={"device_id": "device-12345", "allergens": ["pollen"]},
            )

        assert response.status_code == 422
        assert fake.profiles == {}
    finally:
        app.dependency_overrides.clear()


def test_allergy_profile_read_returns_empty_for_unknown_device() -> None:
    fake = FakeAllergyService()
    app.dependency_overrides[get_allergy_service] = lambda: fake

    try:
        with TestClient(app) as client:
            response = client.get("/api/profile/allergies", params={"device_id": "device-99999"})

        assert response.status_code == 200
        assert response.json() == {
            "device_id": "device-99999",
            "allergens": [],
            "updated_at": None,
        }
    finally:
        app.dependency_overrides.clear()
