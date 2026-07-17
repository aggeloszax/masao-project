from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import device_log_hash, get_chat_ip_rate_limiter, get_chat_rate_limiter, get_chat_service
from api.schemas.chat import ChatRequest, ChatResponse
from api.services.chat_service import ChatService
from api.services.rate_limiter import (
    RateLimitBackendError,
    RateLimitDecision,
    RateLimiter,
    chat_ip_rate_limit_key,
    chat_rate_limit_key,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(
    request: ChatRequest,
    response: Response,
    http_request: Request,
    service: ChatService = Depends(get_chat_service),
    rate_limiter: RateLimiter = Depends(get_chat_rate_limiter),
    ip_rate_limiter: RateLimiter = Depends(get_chat_ip_rate_limiter),
) -> ChatResponse:
    """Handle a restaurant chatbot message from the Next.js client.

    Args:
        request: JSON body sent by the frontend.
        service: Chat orchestration service.

    Returns:
        ChatResponse: Structured response ready for chat bubble rendering.

    Raises:
        HTTPException: 429 for rate limit, 422 for unsupported restaurant, 500 for database failures.
    """
    try:
        decision = await rate_limiter.check(chat_rate_limit_key(request))
        set_rate_limit_headers(response, decision)
        if not decision.allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many chat messages. Please wait before trying again.",
                headers=rate_limit_headers(decision),
            )

        client_host = http_request.client.host if http_request.client is not None else "unknown"
        ip_decision = await ip_rate_limiter.check(chat_ip_rate_limit_key(client_host))
        if not ip_decision.allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many chat messages from this network. Please wait before trying again.",
                headers=rate_limit_headers(ip_decision),
            )

        return await service.handle_chat(request)
    except RateLimitBackendError as exc:
        log_rate_limit_backend_error(table_number=request.table_number, device_id=request.device_id)
        raise HTTPException(status_code=503, detail="Rate limit service unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        log_chat_backend_error(table_number=request.table_number, device_id=request.device_id)
        raise HTTPException(status_code=500, detail="Chat service unavailable") from exc


def log_rate_limit_backend_error(table_number: int, device_id: str) -> None:
    """Log rate limiter failures without raw anonymous device ids.

    Args:
        table_number: Restaurant table number.
        device_id: Raw anonymous frontend device id.

    Returns:
        None.

    Raises:
        None.
    """
    logger.exception(
        "Rate limit backend unavailable for table=%s device_hash=%s",
        table_number,
        device_log_hash(device_id),
    )


def log_chat_backend_error(table_number: int, device_id: str) -> None:
    """Log chat failures without raw anonymous device ids.

    Args:
        table_number: Restaurant table number.
        device_id: Raw anonymous frontend device id.

    Returns:
        None.

    Raises:
        None.
    """
    logger.exception(
        "Chat endpoint failed for table=%s device_hash=%s",
        table_number,
        device_log_hash(device_id),
    )


def rate_limit_headers(decision: RateLimitDecision) -> dict[str, str]:
    """Build response headers for rate-limit decisions.

    Args:
        decision: Rate limiter decision.

    Returns:
        dict[str, str]: Headers for successful and throttled responses.

    Raises:
        None.
    """
    headers = {
        "X-RateLimit-Limit": str(decision.limit),
        "X-RateLimit-Remaining": str(decision.remaining),
        "X-RateLimit-Reset": str(decision.reset_seconds),
    }
    if decision.retry_after_seconds is not None:
        headers["Retry-After"] = str(decision.retry_after_seconds)
    return headers


def set_rate_limit_headers(response: Response, decision: RateLimitDecision) -> None:
    """Attach rate-limit headers to a successful FastAPI response.

    Args:
        response: FastAPI response object.
        decision: Rate limiter decision.

    Returns:
        None.

    Raises:
        None.
    """
    for name, value in rate_limit_headers(decision).items():
        response.headers[name] = value
