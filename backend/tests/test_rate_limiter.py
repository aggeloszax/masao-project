import pytest

from api.routers.chat import rate_limit_headers
from api.schemas.chat import ChatRequest
from api.services.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitBackendError,
    RateLimitDecision,
    RedisRateLimiter,
    chat_ip_rate_limit_key,
    chat_rate_limit_key,
)


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit_until_window_resets() -> None:
    now = [100.0]
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60, max_buckets=100, clock=lambda: now[0])

    first = await limiter.check("chat:device-1")
    second = await limiter.check("chat:device-1")
    third = await limiter.check("chat:device-1")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds == 60

    now[0] = 161.0
    reset = await limiter.check("chat:device-1")

    assert reset.allowed is True
    assert reset.remaining == 1


@pytest.mark.asyncio
async def test_rate_limiter_scopes_limits_by_key() -> None:
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, max_buckets=100)

    first_key = await limiter.check("chat:device-1")
    second_key = await limiter.check("chat:device-2")
    first_key_again = await limiter.check("chat:device-1")

    assert first_key.allowed is True
    assert second_key.allowed is True
    assert first_key_again.allowed is False


def test_chat_rate_limit_key_uses_restaurant_table_and_device() -> None:
    request = ChatRequest(
        restaurant_slug="masao",
        table_number=12,
        device_id="device-12345",
        user_message="hello",
        language_code="en",
    )

    assert chat_rate_limit_key(request) == "chat:masao:12:device-12345"


def test_chat_ip_rate_limit_key_does_not_expose_raw_ip() -> None:
    key = chat_ip_rate_limit_key("203.0.113.42")

    assert key.startswith("chat:ip:")
    assert "203.0.113.42" not in key
    assert key == chat_ip_rate_limit_key("203.0.113.42")


def test_rate_limit_headers_include_retry_after_only_when_blocked() -> None:
    allowed = RateLimitDecision(allowed=True, limit=20, remaining=19, reset_seconds=60)
    blocked = RateLimitDecision(
        allowed=False,
        limit=20,
        remaining=0,
        reset_seconds=42,
        retry_after_seconds=42,
    )

    assert rate_limit_headers(allowed) == {
        "X-RateLimit-Limit": "20",
        "X-RateLimit-Remaining": "19",
        "X-RateLimit-Reset": "60",
    }
    assert rate_limit_headers(blocked)["Retry-After"] == "42"


class FakeRedisClient:
    def __init__(self, result: list[int]) -> None:
        self.result = result
        self.calls: list[tuple[object, ...]] = []
        self.closed = False

    async def eval(self, *args: object) -> list[int]:
        self.calls.append(args)
        return self.result

    async def aclose(self) -> None:
        self.closed = True


class FailingRedisClient:
    async def eval(self, *args: object) -> list[int]:
        raise ConnectionError("redis unavailable")


@pytest.mark.asyncio
async def test_redis_rate_limiter_allows_request_from_eval_result() -> None:
    fake_redis = FakeRedisClient([1, 20, 19, 60, -1])
    limiter = RedisRateLimiter(
        redis_url="redis://unused",
        limit=20,
        window_seconds=60,
        key_prefix="masao",
        socket_timeout_seconds=1.0,
        redis_client=fake_redis,
        clock=lambda: 100.0,
    )

    decision = await limiter.check("chat:masao:12:device-12345")
    await limiter.aclose()

    assert decision == RateLimitDecision(allowed=True, limit=20, remaining=19, reset_seconds=60)
    redis_key = fake_redis.calls[0][2]
    assert isinstance(redis_key, str)
    assert redis_key.startswith("masao:rate_limit:")
    assert "device-12345" not in redis_key
    assert fake_redis.closed is True


@pytest.mark.asyncio
async def test_redis_rate_limiter_blocks_request_from_eval_result() -> None:
    fake_redis = FakeRedisClient([0, 20, 0, 42, 42])
    limiter = RedisRateLimiter(
        redis_url="redis://unused",
        limit=20,
        window_seconds=60,
        key_prefix="masao",
        socket_timeout_seconds=1.0,
        redis_client=fake_redis,
    )

    decision = await limiter.check("chat:masao:12:device-12345")

    assert decision.allowed is False
    assert decision.retry_after_seconds == 42


@pytest.mark.asyncio
async def test_redis_rate_limiter_fail_closed_raises_backend_error() -> None:
    limiter = RedisRateLimiter(
        redis_url="redis://unused",
        limit=20,
        window_seconds=60,
        key_prefix="masao",
        socket_timeout_seconds=1.0,
        fail_closed=True,
        redis_client=FailingRedisClient(),
    )

    with pytest.raises(RateLimitBackendError):
        await limiter.check("chat:masao:12:device-12345")


@pytest.mark.asyncio
async def test_redis_rate_limiter_fail_open_allows_request() -> None:
    limiter = RedisRateLimiter(
        redis_url="redis://unused",
        limit=20,
        window_seconds=60,
        key_prefix="masao",
        socket_timeout_seconds=1.0,
        fail_closed=False,
        redis_client=FailingRedisClient(),
    )

    decision = await limiter.check("chat:masao:12:device-12345")

    assert decision.allowed is True
    assert decision.remaining == 20
