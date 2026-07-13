"""Το chat δεν πρέπει να κρατά DB connection όσο τρέχει η κλήση στο LLM.

Το pool έχει pool_size+max_overflow=30 slots και η κλήση στο Claude κρατά
2-6s· χωρίς commit πριν το LLM, ~30 ταυτόχρονα μηνύματα αρκούν για pool
exhaustion (αναμονή pool_timeout=30s και μετά 500).
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from api.schemas.chat import ChatRequest
from api.services import chat_service as chat_service_module
from api.services.chat_service import ChatService
from api.services.llm_service import LlmAnswer

SESSION_ID = uuid4()
NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)

MENU_ROW = {
    "id": 1,
    "external_id": "C001",
    "category_id": 10,
    "category_slug": "sushi",
    "category_name": "Sushi",
    "category_display_order": 1,
    "name": "Salmon Roll",
    "description": "salmon",
    "price": 9.5,
    "tags": ["fresh"],
    "allergens": ["fish"],
    "is_available": True,
    "display_order": 1,
    "language_code": "en",
}


class FakeResult:
    def __init__(self, rows: list[dict], scalar=None) -> None:
        self._rows = rows
        self._scalar = scalar

    def mappings(self):
        return self

    def all(self) -> list[dict]:
        return self._rows

    def one(self) -> dict:
        return self._rows[0]

    def one_or_none(self) -> dict | None:
        return self._rows[0] if self._rows else None

    def scalar_one(self):
        return self._scalar


class ScriptedSession:
    """Δρομολογεί κάθε SQL στο σωστό αποτέλεσμα και καταγράφει τη σειρά κλήσεων."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.info: dict = {}
        self._message_id = 0

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def commit(self) -> None:
        self.calls.append("commit")

    async def execute(self, statement, params=None) -> FakeResult:
        sql = " ".join(str(statement).split())
        if "insert into chat_sessions" in sql:
            return FakeResult([], scalar=SESSION_ID)
        if "insert into chat_messages" in sql:
            self._message_id += 1
            return FakeResult(
                [
                    {
                        "id": self._message_id,
                        "session_id": SESSION_ID,
                        "role": params["role"],
                        "content": params["content"],
                        "created_at": NOW,
                    }
                ]
            )
        if "from chat_messages" in sql:
            return FakeResult(
                [
                    {
                        "id": 1,
                        "session_id": SESSION_ID,
                        "role": "user",
                        "content": "shrimp please",
                        "created_at": NOW,
                    }
                ]
            )
        if "from customer_allergy_profiles" in sql:
            return FakeResult([])
        if "from menu_items" in sql:
            return FakeResult([MENU_ROW])
        raise AssertionError(f"unexpected SQL: {sql}")


@pytest.mark.asyncio
async def test_handle_chat_commits_before_calling_the_llm(monkeypatch) -> None:
    calls: list[str] = []

    class FakeLlm:
        def is_configured(self) -> bool:
            return True

        async def answer(self, history, menu_items, language_code, customer_allergens=None):
            calls.append("llm")
            return LlmAnswer(reply="Enjoy!", recommended_item_ids=[])

    monkeypatch.setattr(chat_service_module, "get_llm_chat_service", lambda: FakeLlm())

    service = ChatService(session=ScriptedSession(calls))
    response = await service.handle_chat(
        ChatRequest(
            restaurant_slug="masao",
            table_number=1,
            device_id="device-12345",
            user_message="shrimp please",
            language_code="en",
        )
    )

    assert "llm" in calls and "commit" in calls
    # Η σύνδεση πρέπει να επιστρέφει στο pool ΠΡΙΝ την αργή κλήση στο LLM.
    assert calls.index("commit") < calls.index("llm")
    assert response.assistant_message.content == "Enjoy!"
