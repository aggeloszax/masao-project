import json

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_admin_menu_service, verify_internal_api_key
from api.main import app
from api.schemas.admin_menu import (
    MenuCategoryAdminDetailResponse,
    MenuItemAdminDetailResponse,
    MenuItemListResponse,
)
from api.services.translation_service import (
    MAX_SUGGESTED_TAGS,
    TranslationService,
    TranslationUnavailableError,
    build_tags_schema,
    get_translation_service,
)

VOCABULARY = ["σολομός", "καυτερό", "τραγανό", "vegan", "sushi"]


class FakeBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [FakeBlock(text)]
        self.stop_reason = "end_turn"


class FakeMessages:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeAnthropicClient:
    def __init__(self, result) -> None:
        self.messages = FakeMessages(result)


def translator_with(result, monkeypatch: pytest.MonkeyPatch) -> TranslationService:
    monkeypatch.setattr("api.services.translation_service.settings.anthropic_api_key", "test-key")
    service = TranslationService()
    service._client = FakeAnthropicClient(result)
    return service


async def suggest(service: TranslationService, vocabulary=VOCABULARY, examples=None) -> list[str]:
    return await service.suggest_tags(
        name="Spicy salmon roll",
        description="Σολομός, sriracha, τραγανό tempura",
        category_name="Sushi",
        vocabulary=vocabulary,
        examples=examples or [],
    )


def test_build_tags_schema_restricts_answers_to_the_vocabulary() -> None:
    schema = build_tags_schema(VOCABULARY)

    assert schema["required"] == ["tags"]
    assert schema["properties"]["tags"]["items"]["enum"] == VOCABULARY


@pytest.mark.asyncio
async def test_suggest_tags_returns_deduplicated_known_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"tags": ["σολομός", " καυτερό ", "σολομός", "invented"]})
    service = translator_with(FakeResponse(payload), monkeypatch)

    assert await suggest(service) == ["σολομός", "καυτερό"]


@pytest.mark.asyncio
async def test_suggest_tags_caps_the_number_of_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    vocabulary = [f"tag{index}" for index in range(10)]
    service = translator_with(FakeResponse(json.dumps({"tags": vocabulary})), monkeypatch)

    assert len(await suggest(service, vocabulary=vocabulary)) == MAX_SUGGESTED_TAGS


@pytest.mark.asyncio
async def test_suggest_tags_sends_vocabulary_and_examples(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse(json.dumps({"tags": ["sushi"]})), monkeypatch)

    await suggest(service, examples=[("Tuna roll", ["τόνος", "sushi"])])

    call = service._client.messages.calls[0]
    prompt = call["messages"][0]["content"]
    assert "- τραγανό" in prompt
    assert "Tuna roll: τόνος, sushi" in prompt
    assert call["output_config"]["format"]["schema"]["properties"]["tags"]["items"]["enum"] == VOCABULARY


@pytest.mark.asyncio
async def test_suggest_tags_skips_the_api_without_a_vocabulary(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(RuntimeError("must not be called"), monkeypatch)

    assert await suggest(service, vocabulary=[]) == []
    assert service._client.messages.calls == []


@pytest.mark.asyncio
async def test_suggest_tags_rejects_a_non_list_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse(json.dumps({"tags": "sushi"})), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await suggest(service)


class FakeTagAdminService:
    def __init__(self, missing_category: bool = False) -> None:
        self.missing_category = missing_category
        self.listed_categories: list[int | None] = []

    async def list_tags(self) -> list[str]:
        return VOCABULARY

    async def get_category(self, category_id: int) -> MenuCategoryAdminDetailResponse:
        if self.missing_category:
            raise LookupError(f"Menu category not found: {category_id}")
        return MenuCategoryAdminDetailResponse(
            id=category_id, name="Sushi", slug="sushi", display_order=1, item_count=2, translations={}
        )

    async def list_items(self, category_id=None, is_available=None, search=None) -> MenuItemListResponse:
        self.listed_categories.append(category_id)
        items = [
            MenuItemAdminDetailResponse(
                id=index,
                external_id=None,
                category_id=category_id,
                category_name="Sushi",
                name=name,
                description="",
                price=10.0,
                tags=tags,
                is_available=True,
                display_order=index,
                translations={},
            )
            for index, (name, tags) in enumerate([("Tuna roll", ["sushi"]), ("Plain rice", [])], start=1)
        ]
        return MenuItemListResponse(total=len(items), items=items)


class FakeTagTranslator:
    def __init__(self, result=None) -> None:
        self.result = result
        self.calls: list[dict] = []

    async def suggest_tags(self, **kwargs) -> list[str]:
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return ["σολομός", "sushi"]


def post_suggest(admin_service, translator, payload: dict):
    app.dependency_overrides[get_admin_menu_service] = lambda: admin_service
    app.dependency_overrides[get_translation_service] = lambda: translator
    app.dependency_overrides[verify_internal_api_key] = lambda: "test-key"
    try:
        with TestClient(app) as client:
            return client.post("/api/admin/menu/items/suggest-tags", json=payload)
    finally:
        app.dependency_overrides.clear()


def test_suggest_tags_route_passes_category_context_and_tagged_examples() -> None:
    translator = FakeTagTranslator()
    response = post_suggest(
        FakeTagAdminService(),
        translator,
        {"name": " Salmon roll ", "description": "Σολομός", "category_id": 3},
    )

    assert response.status_code == 200
    assert response.json() == {"tags": ["σολομός", "sushi"]}
    call = translator.calls[0]
    assert call["name"] == "Salmon roll"
    assert call["category_name"] == "Sushi"
    assert call["vocabulary"] == VOCABULARY
    assert call["examples"] == [("Tuna roll", ["sushi"])]


def test_suggest_tags_route_tolerates_an_unknown_category() -> None:
    admin_service = FakeTagAdminService(missing_category=True)
    translator = FakeTagTranslator()
    response = post_suggest(admin_service, translator, {"name": "Salmon roll", "category_id": 99})

    assert response.status_code == 200
    assert translator.calls[0]["category_name"] == ""
    assert admin_service.listed_categories == []


def test_suggest_tags_route_requires_some_text() -> None:
    translator = FakeTagTranslator()
    response = post_suggest(FakeTagAdminService(), translator, {"name": "  ", "description": ""})

    assert response.status_code == 422
    assert translator.calls == []


def test_suggest_tags_route_returns_503_when_claude_fails() -> None:
    translator = FakeTagTranslator(TranslationUnavailableError("no api key"))
    response = post_suggest(FakeTagAdminService(), translator, {"name": "Salmon roll"})

    assert response.status_code == 503
