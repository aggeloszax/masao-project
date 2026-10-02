from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from api.schemas.menu import LanguageCode

# Επιτρέπονται ψηφία, κενά και τα συνήθη σύμβολα τηλεφώνου. Δεν επιβάλλουμε
# ελληνικό format: οι πελάτες είναι και τουρίστες με ξένους αριθμούς.
PHONE_PATTERN = re.compile(r"^[0-9+()\-.\s]{5,40}$")


class TakeawayOrderItemRequest(BaseModel):
    """One requested line. Η τιμή ΔΕΝ έρχεται από τον client."""

    item_ref: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., gt=0)
    note: str = Field(default="", max_length=120)

    @field_validator("item_ref")
    @classmethod
    def strip_item_ref(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("item_ref cannot be blank")
        return stripped

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        return value.strip()


class TakeawayOrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=120)
    customer_phone: str = Field(..., min_length=5, max_length=40)
    language_code: LanguageCode = "el"
    items: list[TakeawayOrderItemRequest] = Field(..., min_length=1)

    @field_validator("customer_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = " ".join(value.split())
        if not stripped:
            raise ValueError("Name cannot be blank")
        return stripped

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        stripped = " ".join(value.split())
        if not PHONE_PATTERN.fullmatch(stripped):
            raise ValueError("Phone number is not valid")
        if sum(character.isdigit() for character in stripped) < 5:
            raise ValueError("Phone number needs at least 5 digits")
        return stripped

    @field_validator("items")
    @classmethod
    def reject_duplicate_items(
        cls, value: list[TakeawayOrderItemRequest]
    ) -> list[TakeawayOrderItemRequest]:
        refs = [item.item_ref for item in value]
        if len(set(refs)) != len(refs):
            raise ValueError("Each item may appear only once")
        return value


class TakeawayOrderLine(BaseModel):
    """A priced line, resolved server-side from the menu."""

    menu_item_id: int
    item_ref: str
    name: str
    unit_price: float
    quantity: int
    note: str
    line_total: float


class TakeawayOrderResponse(BaseModel):
    order_id: UUID
    total: float
    items: list[TakeawayOrderLine]
    notified: bool
