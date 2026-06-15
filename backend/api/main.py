from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from api.config import settings
from api.dependencies import check_chat_rate_limiter_ready, close_chat_rate_limiter
from api.routers import admin_menu, chat, menu
from database import close_database, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting up", settings.app_name)
    yield
    await close_chat_rate_limiter()
    await close_database()
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="Masao internal/public data services for the restaurant chatbot MVP",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    allow_credentials=False,
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(menu.router, prefix="/api", tags=["Menu"])
app.include_router(admin_menu.router, prefix="/api/admin", tags=["Admin Menu"])


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a request id and write one structured access log entry.

    Args:
        request: Incoming HTTP request.
        call_next: FastAPI middleware continuation.

    Returns:
        Response: Downstream response with X-Request-ID header.

    Raises:
        Exception: Re-raises downstream exceptions after logging context.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "HTTP request failed request_id=%s method=%s path=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "HTTP request request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "restaurant": settings.restaurant_slug}


async def check_database_ready() -> None:
    """Check that the database accepts a trivial query.

    Args:
        None.

    Returns:
        None.

    Raises:
        Exception: If the database connection or query fails.
    """
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))


async def check_rate_limiter_ready() -> None:
    """Check that the configured rate limiter backend is ready.

    Args:
        None.

    Returns:
        None.

    Raises:
        Exception: If the limiter backend is unavailable.
    """
    await check_chat_rate_limiter_ready()


@app.get("/ready", response_model=None)
async def ready() -> JSONResponse:
    """Return dependency readiness for Render routing checks.

    Args:
        None.

    Returns:
        JSONResponse: Ready payload or 503 not-ready payload.

    Raises:
        None.
    """
    checks = {"database": "ok", "rate_limiter": "ok"}

    try:
        await check_database_ready()
    except Exception:
        logger.exception("Readiness database check failed")
        checks["database"] = "unavailable"

    try:
        await check_rate_limiter_ready()
    except Exception:
        logger.exception("Readiness rate limiter check failed")
        checks["rate_limiter"] = "unavailable"

    if any(value != "ok" for value in checks.values()):
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": settings.app_name, "checks": checks},
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "service": settings.app_name, "checks": checks},
    )
