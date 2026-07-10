from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import device_log_hash, get_allergy_service
from api.schemas.allergy import (
    AllergenListResponse,
    AllergenOption,
    AllergyProfileResponse,
    AllergyProfileUpsertRequest,
)
from api.schemas.menu import LanguageCode
from api.services.allergens import ALLERGEN_CODES, allergen_labels
from api.services.allergy_service import AllergyService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/allergens", response_model=AllergenListResponse, status_code=200)
async def list_allergens(language_code: LanguageCode = Query(default="el")) -> AllergenListResponse:
    """Return the canonical allergen catalogue for the frontend picker.

    Args:
        language_code: Language for the allergen display labels.

    Returns:
        AllergenListResponse: The 14 EU allergen codes with localized labels.

    Raises:
        None.
    """
    labels = allergen_labels(language_code)
    return AllergenListResponse(
        language_code=language_code,
        allergens=[AllergenOption(code=code, label=labels[code]) for code in ALLERGEN_CODES],
    )


@router.get("/profile/allergies", response_model=AllergyProfileResponse, status_code=200)
async def get_allergy_profile(
    device_id: str = Query(..., min_length=8, max_length=128),
    service: AllergyService = Depends(get_allergy_service),
) -> AllergyProfileResponse:
    """Return the stored allergy profile of an anonymous device.

    Args:
        device_id: Anonymous frontend device id.
        service: Allergy data service bound to the current DB session.

    Returns:
        AllergyProfileResponse: Declared allergens (empty list when none).

    Raises:
        HTTPException: 500 for database failures.
    """
    try:
        return await service.get_profile(device_id.strip())
    except SQLAlchemyError as exc:
        logger.exception("Allergy profile read failed for device_hash=%s", device_log_hash(device_id))
        raise HTTPException(status_code=500, detail="Allergy service unavailable") from exc


@router.put("/profile/allergies", response_model=AllergyProfileResponse, status_code=200)
async def upsert_allergy_profile(
    request: AllergyProfileUpsertRequest,
    service: AllergyService = Depends(get_allergy_service),
) -> AllergyProfileResponse:
    """Create or replace the allergy profile of an anonymous device.

    Args:
        request: Device id and canonical allergen codes.
        service: Allergy data service bound to the current DB session.

    Returns:
        AllergyProfileResponse: The stored profile after the upsert.

    Raises:
        HTTPException: 500 for database failures.
    """
    try:
        return await service.upsert_profile(request.device_id, request.allergens)
    except SQLAlchemyError as exc:
        logger.exception("Allergy profile upsert failed for device_hash=%s", device_log_hash(request.device_id))
        raise HTTPException(status_code=500, detail="Allergy service unavailable") from exc
