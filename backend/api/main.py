from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.dependencies import close_chat_rate_limiter
from api.routers import admin_menu, chat, menu
from database import close_database

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "restaurant": settings.restaurant_slug}
