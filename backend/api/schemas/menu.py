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
    categories: list[MenuCategoryPublicResponse]
