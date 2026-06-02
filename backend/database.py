from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from api.config import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout_seconds,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI dependencies.

    Args:
        None.

    Yields:
        AsyncSession: SQLAlchemy async session bound to the configured pool.

    Raises:
        Exception: Re-raises database errors after rolling back the transaction.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Database session failed and was rolled back")
            raise


async def close_database() -> None:
    """Dispose the async database pool during application shutdown.

    Args:
        None.

    Returns:
        None.

    Raises:
        Exception: If SQLAlchemy cannot dispose the engine cleanly.
    """
    await engine.dispose()
