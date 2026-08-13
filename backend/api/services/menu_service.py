from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from sqlalchemy import RowMapping, event, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as OrmSession

from api.config import settings
from api.schemas.menu import MenuCategoryPublicResponse, MenuItemPublicResponse, MenuResponse


class MenuCache:
    """In-process TTL cache for menu rows per language.

    Το μενού αλλάζει σπάνια αλλά διαβάζεται σε κάθε chat μήνυμα και κάθε
    άνοιγμα του μενού· το cache γλιτώνει το 4-πινάκων query στο hot path.
    Η ακύρωση από admin writes είναι best effort (per process)· το TTL
    φράσσει το staleness σε multi-worker deployments.
    """

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._entries: dict[str, tuple[float, list[MenuItemRecord]]] = {}

    def get(self, language_code: str, ttl_seconds: float) -> list[MenuItemRecord] | None:
        """Return cached rows for a language if they are still fresh.

        Args:
            language_code: Menu translation language.
            ttl_seconds: Freshness window; 0 disables caching entirely.

        Returns:
            list[MenuItemRecord] | None: Cached rows, or None on miss/expiry.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return None
        entry = self._entries.get(language_code)
        if entry is None:
            return None
        stored_at, items = entry
        if self._clock() - stored_at > ttl_seconds:
            self._entries.pop(language_code, None)
            return None
        return items

    def store(self, language_code: str, items: list[MenuItemRecord], ttl_seconds: float) -> None:
        """Cache menu rows for a language.

        Args:
            language_code: Menu translation language.
            items: Menu records to reuse across requests. Θεώρησέ τα αμετάβλητα:
                τα ίδια αντικείμενα (και οι εσωτερικές λίστες tags)
                μοιράζονται σε όλα τα requests μέχρι το invalidate/TTL.
            ttl_seconds: Cache policy; 0 or less disables storing entirely.

        Returns:
            None.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return
        self._entries[language_code] = (self._clock(), items)

    def invalidate(self) -> None:
        """Drop every cached language after a menu mutation.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self._entries.clear()


menu_cache = MenuCache()

# Session.info key: τα admin writes το θέτουν και το cache ακυρώνεται ΜΕΤΑ το
# commit. Ακύρωση πριν το commit άφηνε race: αναγνώστης ξαναγέμιζε το cache με
# τα προ-commit (παλιά) δεδομένα που επιβίωναν μέχρι το TTL.
MENU_CACHE_DIRTY_KEY = "menu_cache_dirty"


@event.listens_for(OrmSession, "after_commit")
def invalidate_menu_cache_after_commit(session: OrmSession) -> None:
    """Invalidate the menu cache once a menu mutation actually commits.

    Args:
        session: ORM session that just committed (sync side of AsyncSession).

    Returns:
        None.

    Raises:
        None.
    """
    if session.info.pop(MENU_CACHE_DIRTY_KEY, False):
        menu_cache.invalidate()


@event.listens_for(OrmSession, "after_rollback")
def clear_menu_cache_flag_after_rollback(session: OrmSession) -> None:
    """Drop the dirty flag when a menu mutation rolls back.

    Args:
        session: ORM session that just rolled back.

    Returns:
        None.

    Raises:
        None.
    """
    session.info.pop(MENU_CACHE_DIRTY_KEY, None)


# Ένα lock ανά γλώσσα: όταν λήγει το TTL με ταυτόχρονα requests, μόνο ένα
# τρέχει το 4-πινάκων query· τα υπόλοιπα διαβάζουν το φρέσκο cache.
_fetch_locks: dict[str, asyncio.Lock] = {}


def _fetch_lock(language_code: str) -> asyncio.Lock:
    """Return the per-language single-flight lock, creating it lazily.

    Args:
        language_code: Menu translation language (φραγμένο σύνολο — LanguageCode).

    Returns:
        asyncio.Lock: Shared lock for that language's cache fills.

    Raises:
        None.
    """
    lock = _fetch_locks.get(language_code)
    if lock is None:
        lock = _fetch_locks.setdefault(language_code, asyncio.Lock())
    return lock


@dataclass(frozen=True)
class MenuCandidate:
    id: int
    external_id: str | None
    category: str
    name: str
    description: str
    price: float
    tags: list[str]
    is_available: bool
    language_code: str


@dataclass(frozen=True)
class MenuItemRecord:
    id: int
    external_id: str | None
    category_id: int
    category_slug: str
    category_name: str
    category_display_order: int
    name: str
    description: str
    price: float
    tags: list[str]
    is_available: bool
    display_order: int
    language_code: str


def group_menu_items(
    items: list[MenuItemRecord],
    include_unavailable: bool = False,
) -> list[MenuCategoryPublicResponse]:
    """Group flat menu rows into frontend-friendly category sections.

    Args:
        items: Ordered menu records fetched from PostgreSQL.
        include_unavailable: Whether unavailable items should remain in the response.

    Returns:
        list[MenuCategoryPublicResponse]: Categories with nested items, preserving database display order.

    Raises:
        None.
    """
    categories: dict[int, MenuCategoryPublicResponse] = {}
    for item in items:
        if not include_unavailable and not item.is_available:
            continue

        category = categories.get(item.category_id)
        if category is None:
            category = MenuCategoryPublicResponse(
                id=item.category_id,
                slug=item.category_slug,
                name=item.category_name,
                display_order=item.category_display_order,
                items=[],
            )
            categories[item.category_id] = category

        category.items.append(
            MenuItemPublicResponse(
                id=item.id,
                external_id=item.external_id,
                category_id=item.category_id,
                category_slug=item.category_slug,
                category_name=item.category_name,
                name=item.name,
                description=item.description,
                price=item.price,
                tags=item.tags,
                is_available=item.is_available,
                display_order=item.display_order,
                language_code=item.language_code,  # type: ignore[arg-type]
            )
        )

    return sorted(categories.values(), key=lambda category: (category.display_order, category.id))


class MenuService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_public_menu(
        self,
        restaurant_slug: str,
        language_code: str,
        include_unavailable: bool = False,
    ) -> MenuResponse:
        """Fetch the public menu grouped for frontend rendering.

        Args:
            restaurant_slug: Restaurant identifier requested by the frontend.
            language_code: Requested translation language.
            include_unavailable: Whether unavailable items should be included.

        Returns:
            MenuResponse: Grouped menu categories and items.

        Raises:
            ValueError: If the restaurant slug is unsupported.
        """
        if restaurant_slug != settings.restaurant_slug:
            raise ValueError(f"Unsupported restaurant_slug: {restaurant_slug}")

        items = await self.fetch_items(language_code=language_code)
        categories = group_menu_items(
            items,
            include_unavailable=include_unavailable,
        )
        return MenuResponse(
            restaurant_slug=restaurant_slug,
            language_code=language_code,  # type: ignore[arg-type]
            total_categories=len(categories),
            total_items=sum(len(category.items) for category in categories),
            categories=categories,
        )

    async def fetch_candidates(self, language_code: str) -> list[MenuCandidate]:
        """Fetch available menu rows for recommendation ranking.

        Args:
            language_code: Requested translation language.

        Returns:
            list[MenuCandidate]: Available menu items in display order.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the database query fails.
        """
        items = await self.fetch_items(language_code=language_code)
        return [
            MenuCandidate(
                id=item.id,
                external_id=item.external_id,
                category=item.category_name,
                name=item.name,
                description=item.description,
                price=item.price,
                tags=item.tags,
                is_available=item.is_available,
                language_code=item.language_code,
            )
            for item in items
            if item.is_available
        ]

    async def fetch_items(self, language_code: str) -> list[MenuItemRecord]:
        """Fetch menu rows with localized category and item text.

        Args:
            language_code: Requested translation language.

        Returns:
            list[MenuItemRecord]: Flat menu rows ordered by category and item display order.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the database query fails.
        """
        cached = menu_cache.get(language_code, settings.menu_cache_ttl_seconds)
        if cached is not None:
            return cached

        # TTL <= 0 σημαίνει cache off (π.χ. tests): χωρίς cache να ξαναγεμίσει,
        # το lock απλώς θα σειριοποιούσε άσκοπα τα queries.
        if settings.menu_cache_ttl_seconds <= 0:
            return await self._query_items(language_code)

        async with _fetch_lock(language_code):
            # Double-check: όσο περιμέναμε το lock, ο πρώτος miss γέμισε το cache.
            cached = menu_cache.get(language_code, settings.menu_cache_ttl_seconds)
            if cached is not None:
                return cached
            items = await self._query_items(language_code)
            menu_cache.store(language_code, items, settings.menu_cache_ttl_seconds)
            return items

    async def _query_items(self, language_code: str) -> list[MenuItemRecord]:
        """Run the 4-table menu query and build the flat records.

        Args:
            language_code: Requested translation language.

        Returns:
            list[MenuItemRecord]: Flat menu rows ordered by category and item display order.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the database query fails.
        """
        result = await self.session.execute(
            text(
                """
                select
                    mi.id,
                    mi.external_id,
                    mc.id as category_id,
                    mc.slug as category_slug,
                    coalesce(mct.name, mc.name) as category_name,
                    mc.display_order as category_display_order,
                    coalesce(mit.name, mi.name) as name,
                    coalesce(mit.description, mi.description) as description,
                    mi.price,
                    mi.tags,
                    mi.is_available,
                    mi.display_order,
                    :language_code as language_code
                from menu_items mi
                join menu_categories mc on mc.id = mi.category_id
                left join menu_item_translations mit
                    on mit.menu_item_id = mi.id
                   and mit.language_code = :language_code
                left join menu_category_translations mct
                    on mct.category_id = mc.id
                   and mct.language_code = :language_code
                order by mc.display_order asc, mi.display_order asc, mi.id asc
                """
            ),
            {"language_code": language_code},
        )
        return [self._item_record(row) for row in result.mappings().all()]

    @staticmethod
    def _item_record(row: RowMapping) -> MenuItemRecord:
        return MenuItemRecord(
            id=row["id"],
            external_id=row["external_id"],
            category_id=row["category_id"],
            category_slug=row["category_slug"],
            category_name=row["category_name"],
            category_display_order=row["category_display_order"],
            name=row["name"],
            description=row["description"],
            price=float(row["price"]),
            tags=list(row["tags"] or []),
            is_available=row["is_available"],
            display_order=row["display_order"],
            language_code=row["language_code"],
        )
