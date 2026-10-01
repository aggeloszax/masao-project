from __future__ import annotations

import json
import logging

from anthropic import AsyncAnthropic

from api.config import settings
from api.services.llm_service import LANGUAGE_NAMES

logger = logging.getLogger(__name__)

# Το σχήμα κρατά ΚΑΘΕ γλώσσα ως translation row, συμπεριλαμβανομένων των
# ελληνικών: τα menu_items.name/description είναι το βασικό κείμενο της
# εγγραφής, χωρίς δηλωμένη γλώσσα (στα σημερινά δεδομένα είναι αγγλικά).
# Άρα και οι εννιά γλώσσες είναι μεταφράσιμοι στόχοι.
TRANSLATABLE_LANGUAGES: tuple[str, ...] = tuple(LANGUAGE_NAMES)

# Ξεχωριστό budget από το chat: μια κλήση επιστρέφει έως 8 γλώσσες μαζί, που
# δεν χωράνε στα 1024 tokens του anthropic_max_tokens.
TRANSLATION_MAX_TOKENS = 4096


class TranslationUnavailableError(Exception):
    """Raised when Claude cannot produce usable menu translations."""


def build_item_schema(language_codes: list[str]) -> dict:
    """Build the JSON schema forcing one name/description pair per language.

    Args:
        language_codes: Target languages requested by the admin.

    Returns:
        dict: JSON schema passed to the Anthropic output config.

    Raises:
        None.
    """
    return {
        "type": "object",
        "properties": {
            code: {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name", "description"],
                "additionalProperties": False,
            }
            for code in language_codes
        },
        "required": list(language_codes),
        "additionalProperties": False,
    }


def build_category_schema(language_codes: list[str]) -> dict:
    """Build the JSON schema forcing one name per language.

    Args:
        language_codes: Target languages requested by the admin.

    Returns:
        dict: JSON schema passed to the Anthropic output config.

    Raises:
        None.
    """
    return {
        "type": "object",
        "properties": {code: {"type": "string"} for code in language_codes},
        "required": list(language_codes),
        "additionalProperties": False,
    }


def resolve_target_languages(requested: list[str] | None, existing: set[str], overwrite: bool) -> list[str]:
    """Decide which languages this translation run should write.

    Args:
        requested: Languages asked for, or None for every supported language.
        existing: Languages that already have a stored translation.
        overwrite: Whether existing translations should be regenerated.

    Returns:
        list[str]: Languages to translate, in the canonical selector order.

    Raises:
        ValueError: If a requested language is not translatable.
    """
    if requested is None:
        targets = list(TRANSLATABLE_LANGUAGES)
    else:
        unsupported = [code for code in requested if code not in TRANSLATABLE_LANGUAGES]
        if unsupported:
            raise ValueError(f"Cannot translate into: {', '.join(sorted(unsupported))}")
        # Σταθερή σειρά ανεξάρτητα από το request, ώστε το ίδιο σύνολο γλωσσών
        # να παράγει πάντα το ίδιο prompt.
        requested_set = set(requested)
        targets = [code for code in TRANSLATABLE_LANGUAGES if code in requested_set]

    if not overwrite:
        targets = [code for code in targets if code not in existing]
    return targets


def language_list(language_codes: list[str]) -> str:
    """Render target languages as prompt-friendly `code (Name)` lines.

    Args:
        language_codes: Target languages.

    Returns:
        str: One bullet per language.

    Raises:
        None.
    """
    return "\n".join(f"- {code} ({LANGUAGE_NAMES[code]})" for code in language_codes)


class TranslationService:
    """Claude-backed translator for menu records."""

    def __init__(self) -> None:
        self._client: AsyncAnthropic | None = None

    def is_configured(self) -> bool:
        """Report whether an Anthropic API key is configured.

        Args:
            None.

        Returns:
            bool: True when automatic translation is available.

        Raises:
            None.
        """
        return bool(settings.anthropic_api_key)

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.anthropic_timeout_seconds,
                max_retries=1,
            )
        return self._client

    async def translate_item(
        self,
        name: str,
        description: str,
        category_name: str,
        language_codes: list[str],
    ) -> dict[str, dict[str, str]]:
        """Translate one menu item into several languages.

        Args:
            name: Greek item name.
            description: Greek item description, possibly empty.
            category_name: Greek category name, used only as context.
            language_codes: Target languages.

        Returns:
            dict[str, dict[str, str]]: Language code to name/description pair.

        Raises:
            TranslationUnavailableError: If the API call fails or returns unusable output.
        """
        prompt = TRANSLATE_ITEM_PROMPT.format(
            name=name,
            description=description or "(empty)",
            category_name=category_name,
            languages=language_list(language_codes),
        )

        data = await self._complete(prompt, build_item_schema(language_codes), language_codes)
        translations: dict[str, dict[str, str]] = {}
        for code in language_codes:
            entry = data[code]
            if not isinstance(entry, dict):
                raise TranslationUnavailableError(f"Malformed {code} translation returned by the translator")
            translated_name = str(entry.get("name", "")).strip()
            if not translated_name:
                raise TranslationUnavailableError(f"Empty {code} name returned by the translator")
            translations[code] = {
                "name": translated_name,
                "description": str(entry.get("description", "")).strip(),
            }
        return translations

    async def translate_category(self, name: str, language_codes: list[str]) -> dict[str, str]:
        """Translate one menu category name into several languages.

        Args:
            name: Greek category name.
            language_codes: Target languages.

        Returns:
            dict[str, str]: Language code to translated category name.

        Raises:
            TranslationUnavailableError: If the API call fails or returns unusable output.
        """
        prompt = TRANSLATE_CATEGORY_PROMPT.format(name=name, languages=language_list(language_codes))

        data = await self._complete(prompt, build_category_schema(language_codes), language_codes)
        translations: dict[str, str] = {}
        for code in language_codes:
            translated_name = str(data[code]).strip()
            if not translated_name:
                raise TranslationUnavailableError(f"Empty {code} name returned by the translator")
            translations[code] = translated_name
        return translations

    async def _complete(self, prompt: str, schema: dict, language_codes: list[str]) -> dict:
        """Run one schema-constrained Claude call and parse its JSON payload.

        Args:
            prompt: Fully rendered translation instructions.
            schema: JSON schema the model must satisfy.
            language_codes: Target languages, used to validate the payload.

        Returns:
            dict: Parsed translation payload keyed by language code.

        Raises:
            TranslationUnavailableError: If the API call fails or returns unusable output.
        """
        if not self.is_configured():
            raise TranslationUnavailableError("ANTHROPIC_API_KEY is not configured")

        try:
            response = await self._get_client().messages.create(
                model=settings.anthropic_model,
                max_tokens=TRANSLATION_MAX_TOKENS,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
        except Exception as exc:  # noqa: BLE001 - κάθε αποτυχία API γίνεται 503 για τον admin
            raise TranslationUnavailableError(f"Anthropic API call failed: {exc}") from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise TranslationUnavailableError("Model refused to translate")

        text = next(
            (block.text for block in response.content if getattr(block, "type", None) == "text"),
            None,
        )
        if not text:
            raise TranslationUnavailableError("Model returned no text content")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TranslationUnavailableError(f"Model returned malformed JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise TranslationUnavailableError("Model did not return a translation object")

        missing = [code for code in language_codes if code not in data]
        if missing:
            raise TranslationUnavailableError(f"Missing translations: {', '.join(missing)}")
        return data


TRANSLATE_ITEM_PROMPT = """
Translate one restaurant menu item into every target language below.
Detect the source language yourself; it is whatever the menu record is written in.

Source record:
name: {name}
description: {description}
category: {category_name}

Target languages:
{languages}

Rules:
- Preserve brand names, cocktail names, Japanese dish names, numbers and units unchanged.
- Translate generic food terms naturally, the way a menu in that language would read.
- Stay faithful to the ingredients: never add, drop or invent any.
- No marketing claims, no explanations, no notes.
- If the source description is empty, return an empty description for every language.
- When a target language matches the source language, return the source text unchanged.
""".strip()

TRANSLATE_CATEGORY_PROMPT = """
Translate one restaurant menu category name into every target language below.
Detect the source language yourself; it is whatever the menu record is written in.

Source record: {name}

Target languages:
{languages}

Rules:
- Use the short label a real menu would print as a section heading.
- Preserve Japanese dish names and brand names unchanged.
- No explanations and no punctuation that the source does not have.
- When a target language matches the source language, return the source text unchanged.
""".strip()


_translation_service = TranslationService()


def get_translation_service() -> TranslationService:
    """Return the shared translation service instance.

    Args:
        None.

    Returns:
        TranslationService: Singleton service reusing one Anthropic client.

    Raises:
        None.
    """
    return _translation_service
