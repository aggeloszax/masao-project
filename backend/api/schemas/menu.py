from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

LanguageCode = Literal["el", "en", "de", "it", "sv"]


class MenuItemPublicResponse(BaseModel):
    id: int
    external_id: str | None
    category_id: int
    category_slug: str
    category_name: str
    name: str
    description: str
    price: float
    tags: list[str]
    is_available: bool
    display_order: int
    language_code: LanguageCode
    # Δηλωμένα αλλεργιογόνα του πιάτου· άδεια λίστα = μη αξιολογημένο πιάτο.
    allergens: list[str] = []
    # Alert πεδία: γεμίζουν μόνο όταν το request συνοδεύεται από device_id
    # με αποθηκευμένο allergy profile.
    matched_allergens: list[str] = []
    allergen_alert: bool = False


class MenuCategoryPublicResponse(BaseModel):
    id: int
    slug: str
    name: str
    display_order: int
    items: list[MenuItemPublicResponse]


class MenuResponse(BaseModel):
    restaurant_slug: str
    language_code: LanguageCode
    total_categories: int
    total_items: int
    # Echo των αλλεργιών που εφαρμόστηκαν στα alerts, για επιβεβαίωση στο UI.
    customer_allergens: list[str] = []
    categories: list[MenuCategoryPublicResponse]
