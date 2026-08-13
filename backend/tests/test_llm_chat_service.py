import json
from types import SimpleNamespace

import pytest

from api.services.llm_service import (
    LlmChatService,
    LlmUnavailableError,
    build_menu_prompt,
    build_persona_prompt,
)
from api.services.menu_service import MenuCandidate


def make_item(item_id: int, name: str, available: bool = True) -> MenuCandidate:
    return MenuCandidate(
        id=item_id,
        external_id=f"X{item_id:03d}",
        category="Sushi",
        name=name,
        description=f"{name} description",
        price=9.5,
        tags=["fresh"],
        is_available=available,
        language_code="en",
    )


class FakeMessages:
    def __init__(self, response) -> None:
        self.response = response
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def make_service(response) -> tuple[LlmChatService, FakeMessages]:
    service = LlmChatService()
    fake_messages = FakeMessages(response)
    service._client = SimpleNamespace(messages=fake_messages)
    return service, fake_messages


def make_response(payload: dict, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=json.dumps(payload))],
    )


def test_build_menu_prompt_lists_available_items_with_ids() -> None:
    prompt = build_menu_prompt([make_item(1, "Salmon Roll"), make_item(2, "Hidden Roll", available=False)])

    assert "id=1 | Salmon Roll | 9.50€" in prompt
    assert "Hidden Roll" not in prompt


def test_build_persona_prompt_targets_guest_language() -> None:
    prompt = build_persona_prompt("de")

    assert "German" in prompt
    assert "Never invent items" in prompt
    assert "confirm directly with restaurant staff" in prompt


@pytest.mark.asyncio
async def test_answer_returns_reply_and_valid_recommendations() -> None:
    items = [make_item(1, "Salmon Roll"), make_item(2, "Tuna Roll")]
    service, fake = make_service(
        make_response({"reply": "Try the Salmon Roll!", "recommended_item_ids": [1, 99]})
    )

    answer = await service.answer(
        history=[("user", "what do you recommend?")],
        menu_items=items,
        language_code="en",
    )

    assert answer.reply == "Try the Salmon Roll!"
    assert answer.recommended_item_ids == [1]
    sent = fake.calls[0]
    assert sent["messages"] == [{"role": "user", "content": "what do you recommend?"}]
    assert "Salmon Roll" in sent["system"][1]["text"]


@pytest.mark.asyncio
async def test_answer_raises_on_refusal() -> None:
    service, _ = make_service(make_response({"reply": "x", "recommended_item_ids": []}, stop_reason="refusal"))

    with pytest.raises(LlmUnavailableError):
        await service.answer(
            history=[("user", "hello")],
            menu_items=[make_item(1, "Salmon Roll")],
            language_code="en",
        )


@pytest.mark.asyncio
async def test_answer_raises_on_malformed_json() -> None:
    response = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text="not json")],
    )
    service, _ = make_service(response)

    with pytest.raises(LlmUnavailableError):
        await service.answer(
            history=[("user", "hello")],
            menu_items=[make_item(1, "Salmon Roll")],
            language_code="en",
        )


@pytest.mark.asyncio
async def test_answer_requires_history_ending_with_user_message() -> None:
    service, _ = make_service(make_response({"reply": "x", "recommended_item_ids": []}))

    with pytest.raises(LlmUnavailableError):
        await service.answer(history=[], menu_items=[], language_code="en")
