from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import get_chat_service
from api.schemas.chat import ChatRequest, ChatResponse
from api.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    """Handle a restaurant chatbot message from the Next.js client.

    Args:
        request: JSON body sent by the frontend.
        service: Chat orchestration service.

    Returns:
        ChatResponse: Structured response ready for chat bubble rendering.

    Raises:
        HTTPException: 422 for unsupported restaurant, 500 for database failures.
    """
    try:
        return await service.handle_chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Chat endpoint failed for table=%s device_id=%s", request.table_number, request.device_id)
        raise HTTPException(status_code=500, detail="Chat service unavailable") from exc
