from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    restaurant_slug: str = Field(..., min_length=1, max_length=80)
    table_number: int = Field(..., ge=1, le=999)
    device_id: str = Field(..., min_length=8, max_length=128)
    user_message: str = Field(..., min_length=1, max_length=1000)
    language_code: Literal["el", "en", "de", "it", "sv"] = "el"

    @field_validator("restaurant_slug", "device_id", "user_message")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()


class ChatMessageResponse(BaseModel):
    id: int
    session_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime


class MenuItemResponse(BaseModel):
    id: int
    external_id: str | None
    category: str
    name: str
    description: str
    price: float
    tags: list[str]
    is_available: bool
    language_code: Literal["el", "en", "de", "it", "sv"]


class ChatResponse(BaseModel):
    session_id: UUID
    restaurant_slug: str
    table_number: int
    device_id: str
    language_code: Literal["el", "en", "de", "it", "sv"]
    assistant_message: ChatMessageResponse
    messages: list[ChatMessageResponse]
    recommended_items: list[MenuItemResponse]
