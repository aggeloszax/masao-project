from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from api.dependencies import get_chat_rate_limiter, get_chat_service
from api.main import app
from api.schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse
from api.services.rate_limiter import InMemoryRateLimiter


class FakeChatService:
    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = uuid4()
        assistant_message = ChatMessageResponse(
            id=1,
            session_id=session_id,
            role="assistant",
            content="Test reply",
            created_at=datetime.now(UTC),
        )
        return ChatResponse(
            session_id=session_id,
            restaurant_slug=request.restaurant_slug,
            table_number=request.table_number,
            device_id=request.device_id,
            language_code=request.language_code,
            assistant_message=assistant_message,
            messages=[assistant_message],
            recommended_items=[],
        )


def test_chat_route_returns_429_when_rate_limit_is_exceeded() -> None:
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, max_buckets=100)
    app.dependency_overrides[get_chat_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()

    payload = {
        "restaurant_slug": "masao",
        "table_number": 12,
        "device_id": "device-12345",
        "user_message": "hello",
        "language_code": "en",
    }

    try:
        with TestClient(app) as client:
            first = client.post("/api/chat", json=payload)
            second = client.post("/api/chat", json=payload)

        assert first.status_code == 200
        assert first.headers["X-RateLimit-Remaining"] == "0"
        assert second.status_code == 429
        assert second.headers["Retry-After"] == "60"
    finally:
        app.dependency_overrides.clear()
