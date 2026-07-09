from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from api.config import settings
from api.services.menu_service import MenuCandidate

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "el": "Greek",
    "en": "English",
    "de": "German",
    "it": "Italian",
    "sv": "Swedish",
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "The assistant reply shown to the guest, written in the guest's language.",
        },
        "recommended_item_ids": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Menu item ids being recommended or discussed. Empty when none apply.",
        },
    },
    "required": ["reply", "recommended_item_ids"],
    "additionalProperties": False,
}


class LlmUnavailableError(Exception):
    """Raised when the LLM cannot produce a usable answer."""


@dataclass(frozen=True)
class LlmAnswer:
    reply: str
    recommended_item_ids: list[int]


def build_persona_prompt(language_code: str) -> str:
    """Build the waiter persona instructions for the system prompt.

    Args:
        language_code: Guest language code (el, en, de, it, sv).

    Returns:
        str: Persona and behaviour rules for the assistant.

    Raises:
        None.
    """
    language_name = LANGUAGE_NAMES.get(language_code, "Greek")
    return (
        f"You are the virtual waiter of {settings.restaurant_display_name}, "
        "a restaurant serving sushi, bao, noodles, burgers, poke bowls, desserts, "
        "cocktails, wines, soft drinks and shisha.\n"
        "Behaviour rules:\n"
        f"- Always reply in {language_name} (language code: {language_code}).\n"
        "- Speak like a warm, experienced waiter who knows the menu by heart. "
        "Be natural and human, not robotic. Keep replies short: 1-4 sentences.\n"
        "- Plain text only: no markdown, no asterisks, no bullet lists — "
        "your reply is shown in a simple chat bubble.\n"
        "- Answer ONLY from the menu provided below. Never invent items, ingredients, "
        "prices or availability. If the menu does not list detailed ingredients for an "
        "item, say you do not have that detail instead of guessing.\n"
        "- Always mention prices in euros exactly as listed.\n"
        "- Recommend at most 3 items at a time and put their ids in recommended_item_ids. "
        "When the guest asks about a specific item, include that item's id. "
        "Leave the list empty for greetings or general questions.\n"
        "- Ask a short follow-up question when it helps (allergies, spice preference, "
        "food vs drink), like a real waiter would.\n"
        "- If the guest asks something unrelated to the restaurant, answer briefly and "
        "politely steer the conversation back to the menu.\n"
    )


def build_menu_prompt(menu_items: list[MenuCandidate]) -> str:
    """Serialize the menu into a compact system-prompt block.

    Args:
        menu_items: Available menu candidates fetched from PostgreSQL.

    Returns:
        str: Menu knowledge block grouped by category.

    Raises:
        None.
    """
    lines: list[str] = ["MENU (the only source of truth):"]
    current_category: str | None = None
    for item in menu_items:
        if not item.is_available:
            continue
        if item.category != current_category:
            current_category = item.category
            lines.append(f"\n## {item.category}")
        tags = f" [tags: {', '.join(item.tags)}]" if item.tags else ""
        description = item.description.strip()
        lines.append(f"- id={item.id} | {item.name} | {item.price:.2f}€ | {description}{tags}")
    return "\n".join(lines)


class LlmChatService:
    """Claude-backed conversational service for the restaurant chatbot."""

    def __init__(self) -> None:
        self._client: AsyncAnthropic | None = None

    def is_configured(self) -> bool:
        """Report whether an Anthropic API key is configured.

        Args:
            None.

        Returns:
            bool: True when LLM answering is enabled.

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

    async def answer(
        self,
        history: list[tuple[str, str]],
        menu_items: list[MenuCandidate],
        language_code: str,
    ) -> LlmAnswer:
        """Generate a menu-grounded assistant reply with Claude.

        Args:
            history: Conversation turns as (role, content) tuples, oldest first,
                ending with the latest user message.
            menu_items: Available menu candidates in the guest's language.
            language_code: Guest language code.

        Returns:
            LlmAnswer: Reply text and validated recommended menu item ids.

        Raises:
            LlmUnavailableError: If the API call fails or returns unusable output.
        """
        if not history or history[-1][0] != "user":
            raise LlmUnavailableError("Conversation history must end with a user message")

        messages = [
            {"role": role, "content": content}
            for role, content in history
            if role in ("user", "assistant") and content.strip()
        ]
        # Το API απαιτεί το πρώτο μήνυμα να είναι user· το όριο ιστορικού μπορεί
        # να κόψει τη συνομιλία στη μέση ενός ζεύγους.
        while messages and messages[0]["role"] != "user":
            messages.pop(0)
        if not messages:
            raise LlmUnavailableError("No usable conversation history")

        try:
            response = await self._get_client().messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.anthropic_max_tokens,
                system=[
                    {"type": "text", "text": build_persona_prompt(language_code)},
                    {
                        "type": "text",
                        "text": build_menu_prompt(menu_items),
                        # Το μενού είναι σταθερό ανά γλώσσα: cache για χαμηλότερο κόστος/latency.
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                messages=messages,
                output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
            )
        except Exception as exc:  # noqa: BLE001 - any API failure falls back to keyword answers
            raise LlmUnavailableError(f"Anthropic API call failed: {exc}") from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise LlmUnavailableError("Model refused to answer")

        text = next(
            (block.text for block in response.content if getattr(block, "type", None) == "text"),
            None,
        )
        if not text:
            raise LlmUnavailableError("Model returned no text content")

        try:
            data = json.loads(text)
            reply = str(data["reply"]).strip()
            raw_ids = data["recommended_item_ids"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise LlmUnavailableError(f"Model returned malformed JSON: {exc}") from exc

        if not reply:
            raise LlmUnavailableError("Model returned an empty reply")

        available_ids = {item.id for item in menu_items if item.is_available}
        recommended_ids = [
            int(item_id) for item_id in raw_ids if isinstance(item_id, int) and item_id in available_ids
        ][:3]

        return LlmAnswer(reply=reply, recommended_item_ids=recommended_ids)


_llm_chat_service = LlmChatService()


def get_llm_chat_service() -> LlmChatService:
    """Return the shared LLM chat service instance.

    Args:
        None.

    Returns:
        LlmChatService: Singleton service.

    Raises:
        None.
    """
    return _llm_chat_service
