from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.allergy import AllergyProfileResponse
from api.services.allergens import to_canonical_order
from api.utils import device_log_hash

logger = logging.getLogger(__name__)


class AllergyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, device_id: str) -> AllergyProfileResponse:
        """Fetch the allergy profile for an anonymous device.

        Args:
            device_id: Anonymous frontend device id.

        Returns:
            AllergyProfileResponse: Stored profile, or an empty allergen list
                when the device has not declared anything yet.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the query fails.
        """
        result = await self.session.execute(
            text(
                """
                select device_id, allergens, updated_at
                from customer_allergy_profiles
                where device_id = :device_id
                """
            ),
            {"device_id": device_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            return AllergyProfileResponse(device_id=device_id, allergens=[], updated_at=None)
        return self._profile_response(row["device_id"], list(row["allergens"] or []), row["updated_at"])

    async def get_customer_allergens(self, device_id: str) -> set[str]:
        """Fetch only the declared allergen codes for alert matching.

        Args:
            device_id: Anonymous frontend device id.

        Returns:
            set[str]: Canonical allergen codes; empty when no profile exists.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the query fails.
        """
        # Ίδιο query path με το get_profile ώστε τα δύο να μη διαφωνούν ποτέ
        # στο ποιοι κωδικοί επιβιώνουν (canonical filtering στο ένα σημείο).
        profile = await self.get_profile(device_id)
        return set(profile.allergens)

    async def try_get_customer_allergens(self, device_id: str) -> set[str]:
        """Fetch declared allergens without letting a failure break the caller.

        Args:
            device_id: Anonymous frontend device id.

        Returns:
            set[str]: Declared allergen codes; empty when the lookup fails.
                Fail-open: το μενού/chat συνεχίζει χωρίς alerts αντί να πέσει
                (π.χ. αν δεν έχει εφαρμοστεί ακόμη το migration 004).

        Raises:
            None.
        """
        try:
            # SAVEPOINT: αποτυχία εδώ δεν πρέπει να αφήσει aborted το
            # transaction για τα επόμενα queries του ίδιου request.
            async with self.session.begin_nested():
                return await self.get_customer_allergens(device_id)
        except SQLAlchemyError:
            logger.warning(
                "Allergy profile lookup failed; continuing without alerts for device_hash=%s",
                device_log_hash(device_id),
                exc_info=True,
            )
            return set()

    async def upsert_profile(self, device_id: str, allergens: list[str]) -> AllergyProfileResponse:
        """Create or replace the allergy profile of a device.

        Args:
            device_id: Anonymous frontend device id.
            allergens: Canonical allergen codes; an empty list clears the profile.

        Returns:
            AllergyProfileResponse: The stored profile after the upsert.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        result = await self.session.execute(
            text(
                """
                insert into customer_allergy_profiles (device_id, allergens)
                values (:device_id, :allergens)
                on conflict (device_id) do update
                set
                    allergens = excluded.allergens,
                    updated_at = now()
                returning device_id, allergens, updated_at
                """
            ),
            {"device_id": device_id, "allergens": allergens},
        )
        row = result.mappings().one()
        return self._profile_response(row["device_id"], list(row["allergens"] or []), row["updated_at"])

    @staticmethod
    def _profile_response(device_id: str, allergens: list[str], updated_at: datetime | None) -> AllergyProfileResponse:
        # Φιλτράρισμα (όχι raise) στην ανάγνωση: μη κανονικός κωδικός στη βάση
        # δεν πρέπει να ρίχνει το endpoint, απλώς αγνοείται στα alerts.
        return AllergyProfileResponse(
            device_id=device_id,
            allergens=to_canonical_order(set(allergens)),
            updated_at=updated_at,
        )
