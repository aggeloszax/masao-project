from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from api.schemas.menu import LanguageCode
from api.services.allergens import normalize_allergens


class AllergyProfileUpsertRequest(BaseModel):
    # Ίδιοι περιορισμοί device_id με το ChatRequest ώστε το προφίλ να
    # κλειδώνει στο ίδιο ανώνυμο id που χρησιμοποιεί ήδη το chat.
    device_id: str = Field(..., min_length=8, max_length=128)
    # Όριο σε ΑΚΑΤΕΡΓΑΣΤΕΣ τιμές πριν το dedup (π.χ. ['fish', 'FISH', ...]),
    # γι' αυτό > 14· το normalize_allergens εγγυάται ≤ 14 κανονικούς κωδικούς.
    allergens: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("device_id")
    @classmethod
    def strip_device_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()

    @field_validator("allergens")
    @classmethod
    def validate_allergens(cls, value: list[str]) -> list[str]:
        return normalize_allergens(value)


class AllergyProfileResponse(BaseModel):
    device_id: str
    allergens: list[str]
    updated_at: datetime | None


class AllergenOption(BaseModel):
    code: str
    label: str


class AllergenListResponse(BaseModel):
    language_code: LanguageCode
    allergens: list[AllergenOption]
