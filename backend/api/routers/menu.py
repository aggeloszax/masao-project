from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from api.config import settings
from api.dependencies import get_menu_service
from api.schemas.menu import LanguageCode, MenuResponse
from api.services.menu_service import MenuService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/menu", response_model=MenuResponse, status_code=200)
async def menu(
    restaurant_slug: str = Query(default=settings.restaurant_slug, min_length=1, max_length=80),
    language_code: LanguageCode = Query(default="el"),
    include_unavailable: bool = Query(default=False),
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """Return the public restaurant menu grouped by category.

    Args:
        restaurant_slug: Restaurant identifier requested by the frontend.
        language_code: Translation language for category and item labels.
        include_unavailable: Whether unavailable items should be returned.
        service: Menu data service bound to the current DB session.

    Returns:
        MenuResponse: Grouped menu response for frontend rendering.

    Raises:
        HTTPException: 422 for unsupported restaurant, 500 for database failures.
    """
    try:
        return await service.get_public_menu(
            restaurant_slug=restaurant_slug,
            language_code=language_code,
            include_unavailable=include_unavailable,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Menu endpoint failed for restaurant=%s language=%s", restaurant_slug, language_code)
        raise HTTPException(status_code=500, detail="Menu service unavailable") from exc
