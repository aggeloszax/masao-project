from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from api.schemas.menu import LanguageCode
from api.services.allergens import normalize_allergens


class NonEmptyPatchModel(BaseModel):
    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "NonEmptyPatchModel":
        """Reject PATCH requests that do not change anything.

        Args:
            None.

        Returns:
            NonEmptyPatchModel: The validated model.

        Raises:
            ValueError: If no field was supplied with a non-null value.
        """
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("At least one field must be provided")
        return self


class MenuCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    display_order: int = Field(default=0, ge=0)

    @field_validator("name", "slug")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class MenuCategoryUpdateRequest(NonEmptyPatchModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name", "slug")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class MenuCategoryAdminResponse(BaseModel):
    id: int
    name: str
    slug: str | None
    display_order: int


class MenuCategoryTranslationUpsertRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class MenuCategoryTranslationResponse(BaseModel):
    category_id: int
    language_code: LanguageCode
    name: str


class MenuItemCreateRequest(BaseModel):
    category_id: int = Field(..., gt=0)
    external_id: str | None = Field(default=None, min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    price: float = Field(..., ge=0)
    tags: list[str] = Field(default_factory=list)
    # Όριο σε ακατέργαστες τιμές πριν το dedup· το validator εγγυάται ≤ 14.
    allergens: list[str] = Field(default_factory=list, max_length=50)
    is_available: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("external_id", "name")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags))

    @field_validator("allergens")
    @classmethod
    def validate_allergens(cls, value: list[str]) -> list[str]:
        return normalize_allergens(value)


class MenuItemUpdateRequest(NonEmptyPatchModel):
    category_id: int | None = Field(default=None, gt=0)
    external_id: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    price: float | None = Field(default=None, ge=0)
    tags: list[str] | None = None
    allergens: list[str] | None = Field(default=None, max_length=50)
    is_available: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("external_id", "name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags))

    @field_validator("allergens")
    @classmethod
    def validate_optional_allergens(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_allergens(value)


class MenuItemAdminResponse(BaseModel):
    id: int
    external_id: str | None
    category_id: int
    name: str
    description: str
    price: float
    tags: list[str]
    allergens: list[str]
    is_available: bool
    display_order: int


class MenuItemTranslationUpsertRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()


class MenuItemTranslationResponse(BaseModel):
    menu_item_id: int
    language_code: LanguageCode
    name: str
    description: str


def patch_payload(model: BaseModel) -> dict[str, Any]:
    """Return only supplied non-null request fields.

    Args:
        model: Pydantic request model.

    Returns:
        dict[str, Any]: Fields that should be persisted.

    Raises:
        None.
    """
    return model.model_dump(exclude_unset=True, exclude_none=True)
