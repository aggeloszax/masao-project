"""Allergen alert behaviour across menu grouping, chat fallback and LLM prompts."""

import json
from types import SimpleNamespace

import pytest

from api.services.chat_service import ChatService, answer_menu_query, append_allergy_warnings
from api.services.llm_service import LlmChatService, build_allergy_prompt, build_menu_prompt
from api.services.menu_service import MenuCandidate, MenuItemRecord, group_menu_items


def make_candidate(item_id: int, name: str, allergens: list[str], category: str = "Sushi") -> MenuCandidate:
    return MenuCandidate(
        id=item_id,
        external_id=f"AL{item_id:03d}",
        category=category,
        name=name,
        description=f"{name} description",
        price=9.5,
        tags=["spicy"],
        is_available=True,
        language_code="en",
        allergens=allergens,
    )


def make_record(item_id: int, name: str, allergens: list[str]) -> MenuItemRecord:
    return MenuItemRecord(
        id=item_id,
        external_id=f"AL{item_id:03d}",
        category_id=10,
        category_slug="sushi",
        category_name="Sushi",
        category_display_order=1,
        name=name,
        description=f"{name} description",
        price=9.5,
        tags=["spicy"],
        is_available=True,
        display_order=item_id,
        language_code="en",
        allergens=allergens,
    )


def test_group_menu_items_flags_matching_allergens() -> None:
    items = [
        make_record(1, "Shrimp Tempura", ["crustaceans", "gluten", "eggs"]),
        make_record(2, "Cucumber Maki", []),
    ]

    categories = group_menu_items(items, customer_allergens={"crustaceans", "milk"})
    flagged, clean = categories[0].items

    assert flagged.allergen_alert is True
    assert flagged.matched_allergens == ["crustaceans"]
    assert flagged.allergens == ["crustaceans", "gluten", "eggs"]
    assert clean.allergen_alert is False
    assert clean.matched_allergens == []


def test_group_menu_items_without_profile_has_no_alerts() -> None:
    items = [make_record(1, "Shrimp Tempura", ["crustaceans"])]

    categories = group_menu_items(items)

    assert categories[0].items[0].allergen_alert is False
    assert categories[0].items[0].allergens == ["crustaceans"]


def test_append_allergy_warnings_adds_localized_warning() -> None:
    item = make_candidate(1, "Shrimp Tempura", ["crustaceans"])

    reply = append_allergy_warnings("Try it!", [item], {"crustaceans"}, language_code="en")

    assert "Warning: Shrimp Tempura contains Crustaceans (shrimp, crab)" in reply


def test_append_allergy_warnings_no_profile_keeps_reply_unchanged() -> None:
    item = make_candidate(1, "Shrimp Tempura", ["crustaceans"])

    assert append_allergy_warnings("Try it!", [item], set()) == "Try it!"


def test_answer_menu_query_warns_on_flagged_recommendation() -> None:
    items = [make_candidate(1, "Shrimp Tempura", ["crustaceans"])]

    answer = answer_menu_query(
        "I want shrimp",
        items,
        language_code="en",
        customer_allergens={"crustaceans"},
    )

    assert answer.recommendations[0].name == "Shrimp Tempura"
    assert "Warning" in answer.reply
    assert "leave it out" in answer.reply


def test_answer_menu_query_item_detail_includes_warning() -> None:
    items = [make_candidate(1, "Shrimp Tempura", ["crustaceans"])]

    answer = answer_menu_query(
        "what's in the shrimp tempura",
        items,
        language_code="en",
        customer_allergens={"crustaceans"},
    )

    assert answer.intent == "item_detail"
    assert "Warning" in answer.reply


def test_category_overview_warns_on_flagged_sample_items() -> None:
    items = [make_candidate(1, "Chardonnay", ["sulphites"], category="White Wines")]

    answer = answer_menu_query(
        "σε κρασιά τι έχετε",
        items,
        language_code="el",
        customer_allergens={"sulphites"},
    )

    assert answer.intent == "category_overview"
    assert "Chardonnay" in answer.reply
    assert "Προσοχή" in answer.reply
    assert "Θειώδη" in answer.reply


@pytest.mark.asyncio
async def test_llm_reply_gets_deterministic_allergy_warning(monkeypatch) -> None:
    from api.schemas.chat import ChatRequest
    from api.services import chat_service as chat_service_module
    from api.services.llm_service import LlmAnswer

    class FakeLlm:
        def is_configured(self) -> bool:
            return True

        async def answer(self, history, menu_items, language_code, customer_allergens=None):
            # Το μοντέλο "ξεχνάει" να προειδοποιήσει παρά την οδηγία.
            return LlmAnswer(reply="Try the Shrimp Tempura!", recommended_item_ids=[1])

    monkeypatch.setattr(chat_service_module, "get_llm_chat_service", lambda: FakeLlm())

    service = ChatService(session=None)
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=1,
        device_id="device-12345",
        user_message="shrimp please",
        language_code="en",
    )

    reply, recommendations = await service._generate_answer(
        request=request,
        menu_items=[make_candidate(1, "Shrimp Tempura", ["crustaceans"])],
        history=[],
        customer_allergens={"crustaceans"},
    )

    assert recommendations[0].name == "Shrimp Tempura"
    assert "Warning: Shrimp Tempura contains Crustaceans" in reply


def test_chat_menu_response_marks_matched_allergens() -> None:
    item = make_candidate(1, "Shrimp Tempura", ["crustaceans", "gluten"])

    response = ChatService._menu_response(item, {"gluten"})

    assert response.allergen_alert is True
    assert response.matched_allergens == ["gluten"]
    assert response.allergens == ["crustaceans", "gluten"]


def test_build_menu_prompt_includes_allergens() -> None:
    prompt = build_menu_prompt([make_candidate(1, "Shrimp Tempura", ["crustaceans", "gluten"])])

    assert "[allergens: crustaceans, gluten]" in prompt


def test_build_allergy_prompt_names_codes_and_localized_labels() -> None:
    prompt = build_allergy_prompt(["crustaceans"], "en")

    assert "crustaceans" in prompt
    assert "Crustaceans (shrimp, crab)" in prompt
    assert "confirm with the staff" in prompt
    assert "leave the ingredient out" in prompt
    assert "Prefer recommending items that do not contain" in prompt


@pytest.mark.asyncio
async def test_llm_answer_puts_allergy_block_after_cached_menu_block() -> None:
    class FakeMessages:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        async def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text=json.dumps({"reply": "ok", "recommended_item_ids": []}),
                    )
                ],
            )

    service = LlmChatService()
    fake_messages = FakeMessages()
    service._client = SimpleNamespace(messages=fake_messages)

    await service.answer(
        history=[("user", "hello")],
        menu_items=[make_candidate(1, "Shrimp Tempura", ["crustaceans"])],
        language_code="en",
        customer_allergens=["crustaceans"],
    )

    system_blocks = fake_messages.calls[0]["system"]
    assert len(system_blocks) == 3
    # Το cached block (menu) πρέπει να προηγείται του per-guest allergy block.
    assert system_blocks[1].get("cache_control") == {"type": "ephemeral"}
    assert "GUEST ALLERGY PROFILE" in system_blocks[2]["text"]
    assert "cache_control" not in system_blocks[2]


@pytest.mark.parametrize("lang", ["el", "en", "de", "it", "sv"])
def test_allergy_warning_keeps_format_placeholders(lang: str) -> None:
    from api.services.chat_service import FALLBACK_TEXTS

    text = FALLBACK_TEXTS[lang]["allergy_warning"]
    assert "{name}" in text
    assert "{allergens}" in text
    # Το leading space είναι load-bearing (γίνεται append σε υπάρχον reply)
    # και το format() πιάνει τυχόν αδέσποτα άγκιστρα από μελλοντικές αλλαγές.
    assert text.startswith(" ")
    formatted = text.format(name="X", allergens="Y")
    assert "X" in formatted and "Y" in formatted
