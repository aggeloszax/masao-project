from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.dependencies import get_admin_menu_service, verify_internal_api_key
from api.schemas.admin_menu import (
    MenuCategoryAdminResponse,
    MenuCategoryCreateRequest,
    MenuCategoryTranslationResponse,
    MenuCategoryTranslationUpsertRequest,
    MenuCategoryUpdateRequest,
    MenuItemAdminResponse,
    MenuItemCreateRequest,
    MenuItemTranslationResponse,
    MenuItemTranslationUpsertRequest,
    MenuItemUpdateRequest,
)
from api.schemas.menu import LanguageCode
from api.services.admin_menu_service import AdminMenuService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


@router.post("/menu/categories", response_model=MenuCategoryAdminResponse, status_code=201)
async def create_category(
    request: MenuCategoryCreateRequest,
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuCategoryAdminResponse:
    """Create a menu category for admin users."""
    try:
        return await service.create_category(request)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Category conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category create failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.patch("/menu/categories/{category_id}", response_model=MenuCategoryAdminResponse)
async def update_category(
    request: MenuCategoryUpdateRequest,
    category_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuCategoryAdminResponse:
    """Update a menu category for admin users."""
    try:
        return await service.update_category(category_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Category conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category update failed for category_id=%s", category_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.put(
    "/menu/categories/{category_id}/translations/{language_code}",
    response_model=MenuCategoryTranslationResponse,
)
async def upsert_category_translation(
    request: MenuCategoryTranslationUpsertRequest,
    category_id: int = Path(..., gt=0),
    language_code: LanguageCode = Path(...),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuCategoryTranslationResponse:
    """Create or update a category translation for admin users."""
    try:
        return await service.upsert_category_translation(category_id, language_code, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Category translation conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category translation upsert failed for category_id=%s", category_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.post("/menu/items", response_model=MenuItemAdminResponse, status_code=201)
async def create_item(
    request: MenuItemCreateRequest,
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuItemAdminResponse:
    """Create a menu item for admin users."""
    try:
        return await service.create_item(request)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Item conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item create failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.patch("/menu/items/{item_id}", response_model=MenuItemAdminResponse)
async def update_item(
    request: MenuItemUpdateRequest,
    item_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuItemAdminResponse:
    """Update a menu item for admin users."""
    try:
        return await service.update_item(item_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Item conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item update failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.put("/menu/items/{item_id}/translations/{language_code}", response_model=MenuItemTranslationResponse)
async def upsert_item_translation(
    request: MenuItemTranslationUpsertRequest,
    item_id: int = Path(..., gt=0),
    language_code: LanguageCode = Path(...),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuItemTranslationResponse:
    """Create or update a menu item translation for admin users."""
    try:
        return await service.upsert_item_translation(item_id, language_code, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Item translation conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item translation upsert failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc
