from __future__ import annotations

import asyncio
import hashlib
import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from api.schemas.chat import ChatRequest


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after_seconds: int | None = None


class RateLimitBackendError(RuntimeError):
    """Raised when the configured rate-limit backend is unavailable."""


class RateLimiter(Protocol):
    async def check(self, key: str) -> RateLimitDecision:
        """Check whether a key is still inside its request budget."""


class ClosableRateLimiter(RateLimiter, Protocol):
    async def aclose(self) -> None:
        """Close underlying network resources."""


class InMemoryRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        max_buckets: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self.clock = clock
        self._buckets: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> RateLimitDecision:
        """Check whether a key is still inside its request budget.

        Args:
            key: Stable anonymous limiter key.

        Returns:
            RateLimitDecision: Allow/deny decision plus response header values.

        Raises:
            None.
        """
        now = self.clock()
        async with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            self._remove_expired(bucket, now)

            if len(bucket) >= self.limit:
                retry_after = self._seconds_until_reset(bucket, now)
                return RateLimitDecision(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_seconds=retry_after,
                    retry_after_seconds=retry_after,
                )

            bucket.append(now)
            remaining = max(self.limit - len(bucket), 0)
            reset_seconds = self._seconds_until_reset(bucket, now)
            self._prune_buckets(now)
            return RateLimitDecision(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_seconds=reset_seconds,
            )

    async def healthcheck(self) -> None:
        """Validate that the in-memory limiter is available.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        return None

    def _remove_expired(self, bucket: deque[float], now: float) -> None:
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def _seconds_until_reset(self, bucket: deque[float], now: float) -> int:
        if not bucket:
            return self.window_seconds
        return max(1, math.ceil(self.window_seconds - (now - bucket[0])))

    def _prune_buckets(self, now: float) -> None:
        if len(self._buckets) <= self.max_buckets:
            return

        for key in list(self._buckets):
            self._remove_expired(self._buckets[key], now)
            if not self._buckets[key]:
                del self._buckets[key]

        while len(self._buckets) > self.max_buckets:
            oldest_key = next(iter(self._buckets))
            del self._buckets[oldest_key]


REDIS_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local ttl_ms = tonumber(ARGV[5])

local cutoff = now_ms - window_ms
redis.call("ZREMRANGEBYSCORE", key, "-inf", cutoff)

local count = redis.call("ZCARD", key)
if count >= limit then
    local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
    local retry_seconds = math.ceil(window_ms / 1000)
    if oldest[2] then
        retry_seconds = math.max(1, math.ceil((window_ms - (now_ms - tonumber(oldest[2]))) / 1000))
    end
    redis.call("PEXPIRE", key, ttl_ms)
    return {0, limit, 0, retry_seconds, retry_seconds}
end

redis.call("ZADD", key, now_ms, member)
redis.call("PEXPIRE", key, ttl_ms)

local new_count = count + 1
local remaining = math.max(0, limit - new_count)
local oldest_after = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
local reset_seconds = math.ceil(window_ms / 1000)
if oldest_after[2] then
    reset_seconds = math.max(1, math.ceil((window_ms - (now_ms - tonumber(oldest_after[2]))) / 1000))
end

return {1, limit, remaining, reset_seconds, -1}
"""


class RedisRateLimiter:
    def __init__(
        self,
        redis_url: str,
        limit: int,
        window_seconds: int,
        key_prefix: str,
        socket_timeout_seconds: float,
        fail_closed: bool = True,
        redis_client: Any | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix.rstrip(":")
        self.fail_closed = fail_closed
        self.clock = clock
        if redis_client is None:
            from redis.asyncio import Redis

            self.redis = Redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=socket_timeout_seconds,
                socket_timeout=socket_timeout_seconds,
            )
        else:
            self.redis = redis_client

    async def check(self, key: str) -> RateLimitDecision:
        """Check a distributed Redis sliding-window rate limit.

        Args:
            key: Stable anonymous limiter key.

        Returns:
            RateLimitDecision: Allow/deny decision plus response header values.

        Raises:
            RateLimitBackendError: If Redis is unavailable and fail_closed is enabled.
        """
        now_ms = int(self.clock() * 1000)
        window_ms = self.window_seconds * 1000
        ttl_ms = window_ms + 60_000
        member = f"{now_ms}:{uuid4()}"

        try:
            raw_result = await self.redis.eval(
                REDIS_SLIDING_WINDOW_SCRIPT,
                1,
                self._redis_key(key),
                now_ms,
                window_ms,
                self.limit,
                member,
                ttl_ms,
            )
        except Exception as exc:
            if self.fail_closed:
                raise RateLimitBackendError("Rate limit backend unavailable") from exc
            return RateLimitDecision(
                allowed=True,
                limit=self.limit,
                remaining=self.limit,
                reset_seconds=self.window_seconds,
            )

        allowed, limit, remaining, reset_seconds, retry_after = [int(value) for value in raw_result]
        return RateLimitDecision(
            allowed=bool(allowed),
            limit=limit,
            remaining=remaining,
            reset_seconds=max(1, reset_seconds),
            retry_after_seconds=None if retry_after < 0 else retry_after,
        )

    async def aclose(self) -> None:
        """Close the Redis client connection pool.

        Args:
            None.

        Returns:
            None.

        Raises:
            Exception: If the Redis client fails during close.
        """
        close = getattr(self.redis, "aclose", None)
        if close is not None:
            await close()

    async def healthcheck(self) -> None:
        """Validate that Redis is reachable.

        Args:
            None.

        Returns:
            None.

        Raises:
            RateLimitBackendError: If Redis cannot be reached.
        """
        try:
            await self.redis.ping()
        except Exception as exc:
            raise RateLimitBackendError("Rate limit backend unavailable") from exc

    def _redis_key(self, key: str) -> str:
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:rate_limit:{hashed_key}"


def chat_rate_limit_key(request: ChatRequest) -> str:
    """Build an anonymous per-device chat rate-limit key.

    Args:
        request: Validated chat request.

    Returns:
        str: Limiter key scoped to restaurant, table and anonymous device id.

    Raises:
        None.
    """
    return f"chat:{request.restaurant_slug}:{request.table_number}:{request.device_id}"
