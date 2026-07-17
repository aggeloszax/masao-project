from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.services.admin_menu_service import AdminMenuService
from api.services.allergy_service import AllergyService
from api.services.chat_service import ChatService
from api.services.menu_service import MenuService
from api.services.rate_limiter import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
# Re-export για τους routers που ήδη το εισάγουν από εδώ.
from api.utils import device_log_hash  # noqa: F401
from database import get_db_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def create_chat_rate_limiter(limit: int | None = None) -> RateLimiter:
    """Create the configured chat rate limiter backend.

    Args:
        None.

    Returns:
        RateLimiter: Redis-backed limiter for production or memory limiter for local development.

    Raises:
        RuntimeError: If Redis is selected without a Redis URL.
    """
    effective_limit = limit if limit is not None else settings.chat_rate_limit_requests

    if settings.chat_rate_limit_backend == "redis":
        if not settings.redis_url:
            raise RuntimeError("RATE_LIMIT_BACKEND=redis requires REDIS_URL")
        return RedisRateLimiter(
            redis_url=settings.redis_url,
            limit=effective_limit,
            window_seconds=settings.chat_rate_limit_window_seconds,
            key_prefix=settings.redis_key_prefix,
            socket_timeout_seconds=settings.redis_socket_timeout_seconds,
            fail_closed=settings.rate_limit_fail_closed,
        )

    if settings.chat_rate_limit_backend == "memory":
        return InMemoryRateLimiter(
            limit=effective_limit,
            window_seconds=settings.chat_rate_limit_window_seconds,
            max_buckets=settings.chat_rate_limit_max_buckets,
        )

    raise RuntimeError(f"Unsupported RATE_LIMIT_BACKEND: {settings.chat_rate_limit_backend}")


chat_rate_limiter = create_chat_rate_limiter()
chat_ip_rate_limiter = create_chat_rate_limiter(limit=settings.chat_ip_rate_limit_requests)


async def verify_internal_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate API key for internal-only endpoints.

    Args:
        api_key: API key sent in the X-API-Key header.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the supplied key does not match configuration.
    """
    if not secrets.compare_digest(api_key, settings.internal_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    """Create a ChatService bound to the current async DB session.

    Args:
        session: Async SQLAlchemy session injected by FastAPI.

    Returns:
        ChatService: Service object for chat orchestration.

    Raises:
        None.
    """
    return ChatService(session=session)


async def get_menu_service(session: AsyncSession = Depends(get_db_session)) -> MenuService:
    """Create a MenuService bound to the current async DB session.

    Args:
        session: Async SQLAlchemy session injected by FastAPI.

    Returns:
        MenuService: Service object for public menu reads.

    Raises:
        None.
    """
    return MenuService(session=session)


async def get_allergy_service(session: AsyncSession = Depends(get_db_session)) -> AllergyService:
    """Create an AllergyService bound to the current async DB session.

    Args:
        session: Async SQLAlchemy session injected by FastAPI.

    Returns:
        AllergyService: Service object for customer allergy profiles.

    Raises:
        None.
    """
    return AllergyService(session=session)


async def get_admin_menu_service(session: AsyncSession = Depends(get_db_session)) -> AdminMenuService:
    """Create an AdminMenuService bound to the current async DB session.

    Args:
        session: Async SQLAlchemy session injected by FastAPI.

    Returns:
        AdminMenuService: Service object for authenticated menu management.

    Raises:
        None.
    """
    return AdminMenuService(session=session)


async def get_chat_rate_limiter() -> RateLimiter:
    """Return the shared chat rate limiter.

    Args:
        None.

    Returns:
        RateLimiter: Configured limiter for public chat requests.

    Raises:
        None.
    """
    return chat_rate_limiter


async def get_chat_ip_rate_limiter() -> RateLimiter:
    """Return the shared per-IP chat rate limiter."""
    return chat_ip_rate_limiter


async def close_chat_rate_limiter() -> None:
    """Close limiter resources during FastAPI shutdown.

    Args:
        None.

    Returns:
        None.

    Raises:
        Exception: If the configured limiter close operation fails.
    """
    for limiter in (chat_rate_limiter, chat_ip_rate_limiter):
        close = getattr(limiter, "aclose", None)
        if close is not None:
            await close()


async def check_chat_rate_limiter_ready() -> None:
    """Check that the configured rate limiter is ready.

    Args:
        None.

    Returns:
        None.

    Raises:
        Exception: If the limiter backend is unavailable.
    """
    for limiter in (chat_rate_limiter, chat_ip_rate_limiter):
        healthcheck = getattr(limiter, "healthcheck", None)
        if healthcheck is not None:
            await healthcheck()
