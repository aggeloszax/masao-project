import pytest
from pydantic import ValidationError

from api.schemas.chat import ChatRequest


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


def test_chat_request_accepts_language_code_from_nextjs() -> None:
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=12,
        device_id="device-12345",
        user_message="I want sushi",
        language_code="en",
    )

    assert request.language_code == "en"


def test_chat_request_rejects_hebrew_language_code() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            restaurant_slug="masao",
            table_number=12,
            device_id="device-12345",
            user_message="hello",
            language_code="he",
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
