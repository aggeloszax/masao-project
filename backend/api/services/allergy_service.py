from __future__ import annotations

import logging
import time
from collections import OrderedDict
from datetime import datetime

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as OrmSession

from api.config import settings
from api.schemas.allergy import AllergyProfileResponse
from api.services.allergens import to_canonical_order
from api.utils import device_log_hash

logger = logging.getLogger(__name__)


class ProfileCache:
    """In-process TTL/LRU cache των δηλωμένων αλλεργιογόνων ανά συσκευή.

    Το προφίλ διαβάζεται σε κάθε chat μήνυμα και κάθε /api/menu?device_id=,
    ενώ αλλάζει σπάνια· με cross-region βάση το lookup κοστίζει ~0.6-0.9s.
    Κρατάει και κενά προφίλ (negative caching) γιατί οι περισσότεροι πελάτες
    δεν έχουν δηλώσει τίποτα. Φραγμένο μέγεθος ώστε 200+ συσκευές να μη
    φουσκώνουν τη μνήμη· invalidation μετά το commit του upsert, staleness
    σε multi-worker deployments φράσσεται από το TTL (όπως το MenuCache).
    """

    def __init__(self, clock=time.monotonic, max_entries: int = 5000) -> None:
        self._clock = clock
        self._max_entries = max_entries
        self._entries: OrderedDict[str, tuple[float, frozenset[str]]] = OrderedDict()

    def get(self, device_id: str, ttl_seconds: float) -> frozenset[str] | None:
        """Return cached allergens for a device if still fresh.

        Args:
            device_id: Anonymous frontend device id.
            ttl_seconds: Freshness window; 0 disables caching entirely.

        Returns:
            frozenset[str] | None: Cached codes (possibly empty), None on miss.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return None
        entry = self._entries.get(device_id)
        if entry is None:
            return None
        stored_at, allergens = entry
        if self._clock() - stored_at > ttl_seconds:
            self._entries.pop(device_id, None)
            return None
        self._entries.move_to_end(device_id)
        return allergens

    def store(self, device_id: str, allergens: set[str], ttl_seconds: float) -> None:
        """Cache the declared allergens of a device.

        Args:
            device_id: Anonymous frontend device id.
            allergens: Canonical codes; an empty set is cached too.
            ttl_seconds: Cache policy; 0 or less disables storing entirely.

        Returns:
            None.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return
        self._entries[device_id] = (self._clock(), frozenset(allergens))
        self._entries.move_to_end(device_id)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def invalidate(self, device_id: str | None = None) -> None:
        """Drop one device entry, or everything when no device is given.

        Args:
            device_id: Device to evict; None clears the whole cache.

        Returns:
            None.

        Raises:
            None.
        """
        if device_id is None:
            self._entries.clear()
        else:
            self._entries.pop(device_id, None)


profile_cache = ProfileCache()

# Session.info key: το upsert_profile προσθέτει εδώ τα device_ids που άλλαξαν
# και το cache ακυρώνεται ΜΕΤΑ το commit (ίδιο pattern με το menu cache —
# ακύρωση πριν το commit θα άφηνε race με αναγνώστες που ξαναγεμίζουν stale).
PROFILE_CACHE_DIRTY_KEY = "allergy_profile_cache_dirty"


@event.listens_for(OrmSession, "after_commit")
def invalidate_profile_cache_after_commit(session: OrmSession) -> None:
    """Invalidate cached profiles once a profile upsert actually commits.

    Args:
        session: ORM session that just committed (sync side of AsyncSession).

    Returns:
        None.

    Raises:
        None.
    """
    for device_id in session.info.pop(PROFILE_CACHE_DIRTY_KEY, ()):
        profile_cache.invalidate(device_id)


@event.listens_for(OrmSession, "after_rollback")
def clear_profile_cache_flag_after_rollback(session: OrmSession) -> None:
    """Drop the dirty flag when a profile upsert rolls back.

    Args:
        session: ORM session that just rolled back.

    Returns:
        None.

    Raises:
        None.
    """
    session.info.pop(PROFILE_CACHE_DIRTY_KEY, None)


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
        ttl_seconds = settings.allergy_profile_cache_ttl_seconds
        cached = profile_cache.get(device_id, ttl_seconds)
        if cached is not None:
            return set(cached)

        try:
            # SAVEPOINT: αποτυχία εδώ δεν πρέπει να αφήσει aborted το
            # transaction για τα επόμενα queries του ίδιου request.
            async with self.session.begin_nested():
                allergens = await self.get_customer_allergens(device_id)
        except SQLAlchemyError:
            logger.warning(
                "Allergy profile lookup failed; continuing without alerts for device_hash=%s",
                device_log_hash(device_id),
                exc_info=True,
            )
            # Οι αποτυχίες ΔΕΝ μπαίνουν στο cache: το επόμενο request ξαναδοκιμάζει.
            return set()

        profile_cache.store(device_id, allergens, ttl_seconds)
        return allergens

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
        # Σημάδεψε το session· το cache ακυρώνεται από τον after_commit listener.
        self.session.info.setdefault(PROFILE_CACHE_DIRTY_KEY, set()).add(device_id)
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
