from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.dependencies import get_admin_menu_service, verify_internal_api_key
from api.schemas.admin_menu import (
    MenuCategoryAdminResponse,
    MenuCategoryCreateRequest,
    MenuCategoryListResponse,
    MenuCategoryTranslationResponse,
    MenuCategoryTranslationUpsertRequest,
    MenuCategoryUpdateRequest,
    MenuItemAdminDetailResponse,
    MenuItemAdminResponse,
    MenuItemCreateRequest,
    MenuItemListResponse,
    MenuItemTranslationResponse,
    MenuItemTranslationValue,
    MenuItemTranslationUpsertRequest,
    MenuItemUpdateRequest,
    MenuReorderRequest,
    MenuReorderResponse,
    TranslateCategoryResponse,
    TranslateItemResponse,
    TranslateRequest,
)
from api.schemas.menu import LanguageCode
from api.services.admin_menu_service import AdminMenuService
from api.services.translation_service import (
    TRANSLATABLE_LANGUAGES,
    TranslationService,
    TranslationUnavailableError,
    get_translation_service,
    resolve_target_languages,
)

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


def plan_translation(request: TranslateRequest, existing: set[str]) -> tuple[list[str], list[str]]:
    """Split the requested languages into ones to translate and ones to skip.

    Args:
        request: Auto-translate options sent by the admin.
        existing: Languages that already have a stored translation.

    Returns:
        tuple[list[str], list[str]]: Languages to translate, and requested languages left untouched.

    Raises:
        HTTPException: 422 if a requested language cannot be translated.
    """
    try:
        targets = resolve_target_languages(request.language_codes, existing, request.overwrite)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    requested = set(request.language_codes) if request.language_codes else set(TRANSLATABLE_LANGUAGES)
    skipped = [code for code in TRANSLATABLE_LANGUAGES if code in requested and code not in targets]
    return targets, skipped


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


@router.get("/menu/categories", response_model=MenuCategoryListResponse)
async def list_categories(
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuCategoryListResponse:
    """List categories with translations and item counts for admin users."""
    try:
        return await service.list_categories()
    except SQLAlchemyError as exc:
        logger.exception("Admin category list failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.put("/menu/categories/reorder", response_model=MenuReorderResponse)
async def reorder_categories(
    request: MenuReorderRequest,
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuReorderResponse:
    """Rewrite category display order to match the supplied id sequence."""
    try:
        return MenuReorderResponse(updated=await service.reorder_categories(request.ids))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category reorder failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.delete("/menu/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> Response:
    """Delete an empty menu category for admin users."""
    try:
        await service.delete_category(category_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Category still has menu items") from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category delete failed for category_id=%s", category_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc
    return Response(status_code=204)


@router.post("/menu/categories/{category_id}/translate", response_model=TranslateCategoryResponse)
async def translate_category(
    request: TranslateRequest,
    category_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
    translator: TranslationService = Depends(get_translation_service),
) -> TranslateCategoryResponse:
    """Fill missing category translations with Claude."""
    try:
        category = await service.get_category(category_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin category translate lookup failed for category_id=%s", category_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc

    targets, skipped = plan_translation(request, set(category.translations))
    if not targets:
        return TranslateCategoryResponse(category_id=category_id, translated=[], skipped=skipped, translations={})

    try:
        translations = await translator.translate_category(category.name, targets)
    except TranslationUnavailableError as exc:
        logger.warning("Automatic category translation failed for category_id=%s: %s", category_id, exc)
        raise HTTPException(status_code=503, detail="Automatic translation is unavailable") from exc

    try:
        for language_code, name in translations.items():
            await service.upsert_category_translation(
                category_id,
                language_code,
                MenuCategoryTranslationUpsertRequest(name=name),
            )
    except SQLAlchemyError as exc:
        logger.exception("Admin category translation persist failed for category_id=%s", category_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc

    return TranslateCategoryResponse(
        category_id=category_id,
        translated=targets,
        skipped=skipped,
        translations=translations,
    )


@router.get("/menu/items", response_model=MenuItemListResponse)
async def list_items(
    category_id: int | None = Query(default=None, gt=0),
    is_available: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=160),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuItemListResponse:
    """List menu items with translations for the admin table."""
    try:
        return await service.list_items(category_id=category_id, is_available=is_available, search=search)
    except SQLAlchemyError as exc:
        logger.exception("Admin item list failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.put("/menu/items/reorder", response_model=MenuReorderResponse)
async def reorder_items(
    request: MenuReorderRequest,
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuReorderResponse:
    """Rewrite item display order to match the supplied id sequence."""
    try:
        return MenuReorderResponse(updated=await service.reorder_items(request.ids))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item reorder failed")
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.get("/menu/items/{item_id}", response_model=MenuItemAdminDetailResponse)
async def get_item(
    item_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> MenuItemAdminDetailResponse:
    """Return one menu item with every stored translation."""
    try:
        return await service.get_item(item_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item fetch failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc


@router.delete("/menu/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
) -> Response:
    """Delete a menu item for admin users."""
    try:
        await service.delete_item(item_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item delete failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc
    return Response(status_code=204)


@router.post("/menu/items/{item_id}/translate", response_model=TranslateItemResponse)
async def translate_item(
    request: TranslateRequest,
    item_id: int = Path(..., gt=0),
    service: AdminMenuService = Depends(get_admin_menu_service),
    translator: TranslationService = Depends(get_translation_service),
) -> TranslateItemResponse:
    """Fill missing item translations with Claude."""
    try:
        item = await service.get_item(item_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Admin item translate lookup failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc

    targets, skipped = plan_translation(request, set(item.translations))
    if not targets:
        return TranslateItemResponse(menu_item_id=item_id, translated=[], skipped=skipped, translations={})

    try:
        translations = await translator.translate_item(
            name=item.name,
            description=item.description,
            category_name=item.category_name,
            language_codes=targets,
        )
    except TranslationUnavailableError as exc:
        logger.warning("Automatic item translation failed for item_id=%s: %s", item_id, exc)
        raise HTTPException(status_code=503, detail="Automatic translation is unavailable") from exc

    try:
        for language_code, value in translations.items():
            await service.upsert_item_translation(
                item_id,
                language_code,
                MenuItemTranslationUpsertRequest(name=value["name"], description=value["description"]),
            )
    except SQLAlchemyError as exc:
        logger.exception("Admin item translation persist failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Admin menu service unavailable") from exc

    return TranslateItemResponse(
        menu_item_id=item_id,
        translated=targets,
        skipped=skipped,
        translations={
            code: MenuItemTranslationValue(name=value["name"], description=value["description"])
            for code, value in translations.items()
        },
    )
