from typing import get_args

import pytest
from pydantic import ValidationError

from api.schemas.chat import ChatRequest
from api.schemas.menu import LanguageCode


def test_chat_request_accepts_nextjs_payload() -> None:
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=12,
        device_id="device-12345",
        user_message="θέλω sushi",
    )

    assert request.restaurant_slug == "masao"
    assert request.table_number == 12
    assert request.language_code == "el"


@pytest.mark.parametrize("code", get_args(LanguageCode))
def test_chat_request_accepts_every_supported_language_code(code: str) -> None:
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=12,
        device_id="device-12345",
        user_message="I want sushi",
        language_code=code,
    )

    assert request.language_code == code


def test_chat_request_accepts_conversation_id_from_nextjs() -> None:
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=12,
        device_id="device-12345",
        conversation_id="conversation-12345",
        user_message="hello",
    )

    assert request.conversation_id == "conversation-12345"


def test_chat_request_rejects_unknown_language_code() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            restaurant_slug="masao",
            table_number=12,
            device_id="device-12345",
            user_message="hello",
            language_code="es",
        )


def test_chat_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            restaurant_slug="masao",
            table_number=12,
            device_id="device-12345",
            user_message="   ",
        )


def test_chat_request_rejects_short_device_id() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            restaurant_slug="masao",
            table_number=12,
            device_id="abc",
            user_message="hello",
        )
