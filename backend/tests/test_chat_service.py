from api.services.chat_service import (
    MenuCandidate,
    build_assistant_reply,
    choose_recommendations,
    expand_terms,
    tokenize,
)


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
