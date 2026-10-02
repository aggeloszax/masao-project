from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import get_order_rate_limiter, get_order_service
from api.routers.chat import rate_limit_headers
from api.schemas.orders import TakeawayOrderRequest, TakeawayOrderResponse
from api.services.email_service import EmailUnavailableError, send_takeaway_order_email
from api.services.order_service import OrderService, OrderValidationError, order_total
from api.services.rate_limiter import RateLimitBackendError, RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()


def order_rate_limit_key(client_host: str) -> str:
    return f"order:ip:{client_host}"


@router.post("/orders/takeaway", response_model=TakeawayOrderResponse, status_code=201)
async def create_takeaway_order(
    request: TakeawayOrderRequest,
    http_request: Request,
    service: OrderService = Depends(get_order_service),
    limiter: RateLimiter = Depends(get_order_rate_limiter),
) -> TakeawayOrderResponse:
    """Price, store and email one take-away order.

    Η σειρά έχει σημασία: η παραγγελία αποθηκεύεται και γίνεται commit ΠΡΙΝ
    επιχειρηθεί το email, ώστε μια αποτυχία στον email provider να αφήνει
    πίσω εγγραφή αντί για χαμένη παραγγελία.

    Args:
        request: Guest payload with contact details and requested lines.
        http_request: Incoming request, used for the per-IP rate limit.
        service: Order persistence service.
        limiter: Per-IP limiter for this public endpoint.

    Returns:
        TakeawayOrderResponse: Stored order id, server-computed total and lines.

    Raises:
        HTTPException: 429 rate limited, 422 invalid lines, 502 email failed, 500/503 infrastructure.
    """
    client_host = http_request.client.host if http_request.client is not None else "unknown"
    try:
        decision = await limiter.check(order_rate_limit_key(client_host))
    except RateLimitBackendError as exc:
        logger.error("Order rate limiter unavailable")
        raise HTTPException(status_code=503, detail="Order service unavailable") from exc

    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many orders from this network. Please wait before trying again.",
            headers=rate_limit_headers(decision),
        )

    try:
        lines = await service.resolve_lines(request.items, request.language_code)
    except OrderValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Order line resolution failed")
        raise HTTPException(status_code=500, detail="Order service unavailable") from exc

    total = order_total(lines)

    try:
        order_id = await service.create_order(request, lines, total)
        await service.session.commit()
    except SQLAlchemyError as exc:
        logger.exception("Order persistence failed")
        raise HTTPException(status_code=500, detail="Order service unavailable") from exc

    try:
        await send_takeaway_order_email(
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            items=lines,
            total=total,
        )
    except EmailUnavailableError as exc:
        # Η παραγγελία υπάρχει ήδη στη βάση· καταγράφουμε γιατί δεν έφυγε το
        # email και το λέμε ειλικρινά στον πελάτη αντί να δείξουμε επιτυχία.
        logger.error("Take-away notification failed for order_id=%s: %s", order_id, exc)
        try:
            await service.mark_email_failed(order_id, str(exc))
            await service.session.commit()
        except SQLAlchemyError:
            logger.exception("Could not record email failure for order_id=%s", order_id)
        raise HTTPException(
            status_code=502,
            detail="Order saved but the restaurant could not be notified. Please call us.",
        ) from exc

    try:
        await service.mark_notified(order_id)
        await service.session.commit()
    except SQLAlchemyError:
        # Το email έφυγε· μια αποτυχία στο flag δεν πρέπει να ακυρώσει την παραγγελία.
        logger.exception("Could not mark order_id=%s as notified", order_id)

    logger.info("Take-away order stored and notified order_id=%s total=%.2f", order_id, total)
    return TakeawayOrderResponse(order_id=order_id, total=total, items=lines, notified=True)
