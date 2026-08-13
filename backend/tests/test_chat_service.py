from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from api.services.chat_service import (
    FALLBACK_TEXTS,
    ChatService,
    MenuCandidate,
    answer_menu_query,
    build_assistant_reply,
    choose_recommendations,
    device_storage_hash,
    expand_terms,
    tokenize,
)


def test_fallback_texts_have_identical_keys_in_every_language() -> None:
    # Guard: αν προστεθεί κλειδί σε μία γλώσσα και ξεχαστεί σε άλλη, το
    # texts["..."] θα σκάσει με KeyError σε παραγωγή για εκείνη τη γλώσσα.
    reference_keys = set(FALLBACK_TEXTS["el"])

    for language_code, texts in FALLBACK_TEXTS.items():
        assert set(texts) == reference_keys, f"key mismatch for {language_code}"


def test_fallback_texts_cover_every_supported_language() -> None:
    # Guard: μια γλώσσα που μπαίνει στο LanguageCode χωρίς fallback κείμενα
    # θα σέρβιρε σιωπηλά ελληνικά (μαζί με το allergy warning) στον guest.
    from typing import get_args

    from api.schemas.menu import LanguageCode
    from api.services.llm_service import LANGUAGE_NAMES

    supported = set(get_args(LanguageCode))
    assert set(FALLBACK_TEXTS) == supported
    assert set(LANGUAGE_NAMES) == supported


def test_device_storage_hash_is_stable_and_does_not_expose_raw_id() -> None:
    raw_device_id = "device-12345678"

    hashed = device_storage_hash(raw_device_id)

    assert hashed == device_storage_hash(raw_device_id)
    assert len(hashed) == 64
    assert raw_device_id not in hashed


@pytest.mark.asyncio
async def test_get_or_create_session_persists_only_hashed_device_id() -> None:
    session_id = uuid4()
    result = MagicMock()
    result.scalar_one.return_value = session_id
    session = AsyncMock()
    session.execute.return_value = result
    service = ChatService(session=session)

    returned_session_id = await service._get_or_create_session("device-12345678", 7)

    params = session.execute.await_args.args[1]
    assert returned_session_id == session_id
    assert params["device_id"] == device_storage_hash("device-12345678")
    assert params["device_id"] != "device-12345678"


@pytest.mark.asyncio
async def test_get_or_create_session_separates_conversations_for_same_device() -> None:
    session_id = uuid4()
    result = MagicMock()
    result.scalar_one.return_value = session_id
    session = AsyncMock()
    session.execute.return_value = result
    service = ChatService(session=session)

    await service._get_or_create_session("device-12345678", 7, "conversation-12345")

    params = session.execute.await_args.args[1]
    assert params["device_id"] == device_storage_hash(
        "device-12345678:conversation-12345"
    )


@pytest.mark.asyncio
async def test_delete_expired_sessions_uses_configured_retention() -> None:
    session = AsyncMock()
    service = ChatService(session=session)

    await service._delete_expired_sessions()

    statement, params = session.execute.await_args.args
    assert "delete from chat_sessions" in str(statement)
    assert params["retention_days"] > 0


def test_tokenize_supports_latin_input() -> None:
    tokens = tokenize("I want something spicy")

    assert "spicy" in tokens


def test_choose_recommendations_happy_path_spicy_shrimp() -> None:
    items = [
        MenuCandidate(
            id=1,
            external_id="UR007",
            category="Sushi",
            name="Shrimp Tempura",
            description="Shrimp tempura with spicy mayo",
            price=9.3,
            tags=["shrimp", "spicy", "crispy"],
            is_available=True,
            language_code="en",
        ),
        MenuCandidate(
            id=2,
            external_id="DE001",
            category="Desserts",
            name="Chocolate Fondant",
            description="Warm chocolate dessert",
            price=7.0,
            tags=["dessert", "sweet"],
            is_available=True,
            language_code="en",
        ),
    ]

    recommendations = choose_recommendations("I want spicy shrimp", items)

    assert [item.name for item in recommendations] == ["Shrimp Tempura"]


def test_choose_recommendations_ignores_unavailable_items() -> None:
    items = [
        MenuCandidate(
            id=1,
            external_id="TEST001",
            category="Sushi",
            name="Unavailable Spicy Roll",
            description="Spicy roll",
            price=5.0,
            tags=["spicy"],
            is_available=False,
            language_code="en",
        )
    ]

    assert choose_recommendations("spicy", items) == []


def test_build_assistant_reply_fallback_for_no_match() -> None:
    reply = build_assistant_reply("unknown request", [])

    assert "sushi" in reply


def test_expand_terms_adds_synonyms_for_spicy() -> None:
    terms = expand_terms(["spicy"])

    assert "hot" in terms
    assert "chilli" in terms


def test_choose_recommendations_scopes_fruity_cocktail_to_cocktails() -> None:
    items = [
        MenuCandidate(
            id=1,
            external_id="CO001",
            category="Masao Cocktails",
            name="Okinawa",
            description="Japanese Yuzu Aperitif, Elderflower, Strawberry",
            price=10.0,
            tags=["fruity", "fresh"],
            is_available=True,
            language_code="en",
        ),
        MenuCandidate(
            id=2,
            external_id="CC009",
            category="Classic Cocktails",
            name="Long Drinks",
            description="Classic long drinks selection",
            price=9.0,
            tags=["fresh", "classic"],
            is_available=True,
            language_code="en",
        ),
        MenuCandidate(
            id=3,
            external_id="DR003",
            category="Soft Drinks",
            name="Three Cents Pink Grapefruit Soda",
            description="Pink grapefruit soda 200ml",
            price=4.0,
            tags=["fruity", "fresh"],
            is_available=True,
            language_code="en",
        ),
    ]

    recommendations = choose_recommendations("θέλω ένα φρουτώδες cocktail", items)

    assert [item.name for item in recommendations] == ["Okinawa"]


def test_answer_menu_query_returns_drink_overview_for_drinks_question() -> None:
    items = [
        MenuCandidate(1, "CO001", "Masao Cocktails", "Okinawa", "Yuzu, Strawberry", 10.0, ["fruity"], True, "en"),
        MenuCandidate(2, "DR004", "Soft Drinks", "Espresso", "Espresso coffee", 3.0, ["coffee"], True, "en"),
        MenuCandidate(3, "WW001", "White Wines", "Oinos Grigoriadi", "Sauvignon Blanc", 32.0, ["dry"], True, "en"),
        MenuCandidate(4, "UR009", "Uramaki / Hossomaki (6pcs)", "Spicy Suzuki", "Sea bass roll", 9.5, ["spicy"], True, "en"),
    ]

    answer = answer_menu_query("σε ποτά τι έχει", items)

    assert answer.intent == "category_overview"
    assert "Cocktails" in answer.reply
    assert "Soft Drinks" in answer.reply
    assert "White Wines" in answer.reply
    assert "Spicy Suzuki" not in answer.reply
    assert answer.recommendations == []


def test_answer_menu_query_returns_long_drinks_detail_without_inventing() -> None:
    items = [
        MenuCandidate(
            id=1,
            external_id="CC009",
            category="Classic Cocktails",
            name="Long Drinks",
            description="Classic Long Drinks",
            price=9.0,
            tags=["fresh", "classic"],
            is_available=True,
            language_code="en",
        ),
        MenuCandidate(
            id=2,
            external_id="DR005",
            category="Soft Drinks",
            name="Tea",
            description="Tea",
            price=3.0,
            tags=["hot"],
            is_available=True,
            language_code="en",
        ),
    ]

    answer = answer_menu_query("τι έχει το long drinks", items)

    assert answer.intent == "item_detail"
    assert answer.recommendations[0].name == "Long Drinks"
    assert "Classic Long Drinks" in answer.reply
    assert "δεν έχω αναλυτικά συστατικά" in answer.reply
    assert "Tea" not in answer.reply


def test_answer_menu_query_returns_exact_item_detail_for_cucumber_maki() -> None:
    items = [
        MenuCandidate(
            id=1,
            external_id="UR001",
            category="Uramaki / Hossomaki (6pcs)",
            name="Cucumber Maki",
            description="cucumber",
            price=8.0,
            tags=["fresh", "vegan"],
            is_available=True,
            language_code="en",
        ),
        MenuCandidate(
            id=2,
            external_id="UR007",
            category="Uramaki / Hossomaki (6pcs)",
            name="Shrimp Tempura",
            description="shrimp tempura, avocado, spicy mayo",
            price=9.3,
            tags=["shrimp", "spicy"],
            is_available=True,
            language_code="en",
        ),
    ]

    answer = answer_menu_query("τι περιέχει το cucumber maki", items)

    assert answer.intent == "item_detail"
    assert answer.recommendations[0].name == "Cucumber Maki"
    assert "cucumber" in answer.reply
    assert "Shrimp Tempura" not in answer.reply
