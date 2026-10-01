import json

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_admin_menu_service, verify_internal_api_key
from api.main import app
from api.schemas.admin_menu import MenuItemAdminDetailResponse, MenuItemTranslationResponse
from api.services.translation_service import (
    TRANSLATABLE_LANGUAGES,
    TranslationService,
    TranslationUnavailableError,
    build_item_schema,
    get_translation_service,
    resolve_target_languages,
)


def test_every_supported_language_is_translatable() -> None:
    # Το σχήμα κρατά και τα ελληνικά ως translation row, όχι ως βάση.
    assert set(TRANSLATABLE_LANGUAGES) == {"el", "en", "de", "it", "sv", "fr", "ru", "he", "tr"}


def test_resolve_target_languages_defaults_to_every_missing_language() -> None:
    targets = resolve_target_languages(None, existing=set(), overwrite=False)

    assert targets == list(TRANSLATABLE_LANGUAGES)


def test_resolve_target_languages_can_fill_greek() -> None:
    targets = resolve_target_languages(None, existing={"en", "de"}, overwrite=False)

    assert "el" in targets


def test_resolve_target_languages_skips_languages_that_already_exist() -> None:
    targets = resolve_target_languages(None, existing={"en", "de"}, overwrite=False)

    assert "en" not in targets
    assert "de" not in targets
    assert "fr" in targets


def test_resolve_target_languages_overwrite_keeps_existing_languages() -> None:
    targets = resolve_target_languages(["en", "de"], existing={"en", "de"}, overwrite=True)

    assert targets == ["en", "de"]


def test_resolve_target_languages_returns_canonical_order_regardless_of_request_order() -> None:
    targets = resolve_target_languages(["tr", "en", "fr"], existing=set(), overwrite=False)

    assert targets == ["en", "fr", "tr"]


def test_resolve_target_languages_rejects_an_unsupported_language() -> None:
    with pytest.raises(ValueError):
        resolve_target_languages(["es"], existing=set(), overwrite=False)


def test_resolve_target_languages_returns_empty_when_nothing_is_missing() -> None:
    assert resolve_target_languages(["en"], existing={"en"}, overwrite=False) == []


def test_build_item_schema_requires_every_target_language() -> None:
    schema = build_item_schema(["en", "de"])

    assert schema["required"] == ["en", "de"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["en"]["required"] == ["name", "description"]


class FakeBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class FakeResponse:
    def __init__(self, text: str, stop_reason: str = "end_turn") -> None:
        self.content = [FakeBlock(text)]
        self.stop_reason = stop_reason


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


@pytest.mark.asyncio
async def test_translate_item_returns_stripped_translations(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        {
            "en": {"name": "  Salmon sashimi  ", "description": " Fresh salmon "},
            "de": {"name": "Lachs-Sashimi", "description": ""},
        }
    )
    service = translator_with(FakeResponse(payload), monkeypatch)

    translations = await service.translate_item(
        name="Σασίμι σολομού",
        description="Φρέσκος σολομός",
        category_name="Σούσι",
        language_codes=["en", "de"],
    )

    assert translations == {
        "en": {"name": "Salmon sashimi", "description": "Fresh salmon"},
        "de": {"name": "Lachs-Sashimi", "description": ""},
    }


@pytest.mark.asyncio
async def test_translate_item_sends_the_schema_for_the_requested_languages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"fr": {"name": "Sashimi de saumon", "description": ""}})
    service = translator_with(FakeResponse(payload), monkeypatch)

    await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["fr"])

    call = service._client.messages.calls[0]
    assert call["output_config"]["format"]["schema"]["required"] == ["fr"]
    assert "French" in call["messages"][0]["content"]


@pytest.mark.asyncio
async def test_translate_item_rejects_a_missing_language(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse(json.dumps({"en": {"name": "X", "description": ""}})), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["en", "de"])


@pytest.mark.asyncio
async def test_translate_item_rejects_an_empty_name(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse(json.dumps({"en": {"name": "   ", "description": "x"}})), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["en"])


@pytest.mark.asyncio
async def test_translate_item_rejects_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse("not json"), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["en"])


@pytest.mark.asyncio
async def test_translate_item_rejects_a_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse("{}", stop_reason="refusal"), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["en"])


@pytest.mark.asyncio
async def test_translate_item_wraps_api_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(RuntimeError("connection reset"), monkeypatch)

    with pytest.raises(TranslationUnavailableError):
        await service.translate_item(name="Σασίμι", description="", category_name="Σούσι", language_codes=["en"])


@pytest.mark.asyncio
async def test_translate_category_returns_plain_names(monkeypatch: pytest.MonkeyPatch) -> None:
    service = translator_with(FakeResponse(json.dumps({"en": " Sushi ", "de": "Sushi"})), monkeypatch)

    translations = await service.translate_category("Σούσι", ["en", "de"])

    assert translations == {"en": "Sushi", "de": "Sushi"}


@pytest.mark.asyncio
async def test_translation_is_unavailable_without_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.services.translation_service.settings.anthropic_api_key", None)
    service = TranslationService()

    assert service.is_configured() is False
    with pytest.raises(TranslationUnavailableError):
        await service.translate_category("Σούσι", ["en"])


class FakeTranslateAdminService:
    def __init__(self, existing_translations: dict) -> None:
        self.existing_translations = existing_translations
        self.upserts: list[tuple[int, str]] = []

    async def get_item(self, item_id: int) -> MenuItemAdminDetailResponse:
        return MenuItemAdminDetailResponse(
            id=item_id,
            external_id="m7",
            category_id=3,
            category_name="Σούσι",
            name="Σασίμι σολομού",
            description="Φρέσκος σολομός",
            price=12.5,
            tags=[],
            is_available=True,
            display_order=1,
            translations=self.existing_translations,
        )

    async def upsert_item_translation(self, item_id, language_code, request) -> MenuItemTranslationResponse:
        self.upserts.append((item_id, language_code))
        return MenuItemTranslationResponse(
            menu_item_id=item_id,
            language_code=language_code,
            name=request.name,
            description=request.description,
        )


class FakeTranslator:
    def __init__(self, result=None) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    async def translate_item(self, name, description, category_name, language_codes):
        self.calls.append(language_codes)
        if isinstance(self.result, Exception):
            raise self.result
        return {code: {"name": f"{code}-name", "description": f"{code}-desc"} for code in language_codes}


def translate_client(admin_service, translator) -> TestClient:
    app.dependency_overrides[get_admin_menu_service] = lambda: admin_service
    app.dependency_overrides[get_translation_service] = lambda: translator
    app.dependency_overrides[verify_internal_api_key] = lambda: "test-key"
    return TestClient(app)


def test_translate_item_route_persists_only_the_missing_languages() -> None:
    admin_service = FakeTranslateAdminService({"en": {"name": "Salmon sashimi", "description": "Fresh"}})
    translator = FakeTranslator()
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post(
                "/api/admin/menu/items/7/translate",
                json={"language_codes": ["en", "de"], "overwrite": False},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["translated"] == ["de"]
    assert body["skipped"] == ["en"]
    assert translator.calls == [["de"]]
    assert admin_service.upserts == [(7, "de")]


def test_translate_item_route_skips_the_api_call_when_nothing_is_missing() -> None:
    admin_service = FakeTranslateAdminService(
        {code: {"name": f"{code}-name", "description": ""} for code in TRANSLATABLE_LANGUAGES}
    )
    translator = FakeTranslator()
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post("/api/admin/menu/items/7/translate", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["translated"] == []
    assert response.json()["skipped"] == list(TRANSLATABLE_LANGUAGES)
    assert translator.calls == []


def test_translate_item_route_overwrite_retranslates_existing_languages() -> None:
    admin_service = FakeTranslateAdminService({"en": {"name": "Salmon sashimi", "description": "Fresh"}})
    translator = FakeTranslator()
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post(
                "/api/admin/menu/items/7/translate",
                json={"language_codes": ["en"], "overwrite": True},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert translator.calls == [["en"]]
    assert admin_service.upserts == [(7, "en")]


def test_translate_item_route_returns_503_when_the_translator_fails() -> None:
    admin_service = FakeTranslateAdminService({})
    translator = FakeTranslator(TranslationUnavailableError("no api key"))
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post("/api/admin/menu/items/7/translate", json={"language_codes": ["de"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert admin_service.upserts == []


def test_translate_item_route_rejects_an_unsupported_language() -> None:
    admin_service = FakeTranslateAdminService({})
    translator = FakeTranslator()
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post("/api/admin/menu/items/7/translate", json={"language_codes": ["es"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert translator.calls == []


def test_translate_item_route_can_fill_greek() -> None:
    admin_service = FakeTranslateAdminService({})
    translator = FakeTranslator()
    try:
        with translate_client(admin_service, translator) as client:
            response = client.post("/api/admin/menu/items/7/translate", json={"language_codes": ["el"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert translator.calls == [["el"]]
    assert admin_service.upserts == [(7, "el")]
