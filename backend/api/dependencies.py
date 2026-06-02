from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.services.chat_service import ChatService
from database import get_db_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_internal_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate API key for internal-only endpoints.

    Args:
        api_key: API key sent in the X-API-Key header.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the supplied key does not match configuration.
    """
    if api_key != settings.internal_api_key:
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
