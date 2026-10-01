from __future__ import annotations

import json
from typing import Any

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.admin_menu import (
    MenuCategoryAdminDetailResponse,
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
    patch_payload,
)
from api.services.menu_service import MENU_CACHE_DIRTY_KEY


def build_update_statement(table_name: str, fields: dict[str, Any], allowed_fields: set[str]) -> tuple[str, dict[str, Any]]:
    """Build a whitelisted SQL UPDATE assignment list.

    Args:
        table_name: Logical table name used only for error messages.
        fields: Request fields after validation.
        allowed_fields: Column names that may be updated.

    Returns:
        tuple[str, dict[str, Any]]: SQL assignment fragment and bind parameters.

    Raises:
        ValueError: If the request has no fields or contains an unsupported field.
    """
    if not fields:
        raise ValueError("At least one field must be provided")

    unknown_fields = set(fields) - allowed_fields
    if unknown_fields:
        raise ValueError(f"Unsupported {table_name} fields: {', '.join(sorted(unknown_fields))}")

    assignments = [f"{field} = :{field}" for field in fields]
    return ", ".join(assignments), dict(fields)


def decode_jsonb_object(value: object) -> dict:
    """Normalize a jsonb aggregate into a plain dict.

    Το asyncpg επιστρέφει jsonb ήδη αποκωδικοποιημένο, αλλά τα aggregates
    χωρίς γραμμές δίνουν NULL και κάποια setups δίνουν raw JSON string.

    Args:
        value: Raw value read from the `translations` column.

    Returns:
        dict: Decoded mapping, empty when the aggregate produced no rows.

    Raises:
        None.
    """
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


class AdminMenuService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _mark_menu_mutated(self) -> None:
        """Schedule menu cache invalidation for after this session commits.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.session.info[MENU_CACHE_DIRTY_KEY] = True

    async def create_category(self, request: MenuCategoryCreateRequest) -> MenuCategoryAdminResponse:
        """Create a menu category.

        Args:
            request: Validated category payload.

        Returns:
            MenuCategoryAdminResponse: Created category row.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        result = await self.session.execute(
            text(
                """
                insert into menu_categories (name, slug, display_order)
                values (:name, :slug, :display_order)
                returning id, name, slug, display_order
                """
            ),
            request.model_dump(),
        )
        self._mark_menu_mutated()
        return self._category_response(result.mappings().one())

    async def update_category(self, category_id: int, request: MenuCategoryUpdateRequest) -> MenuCategoryAdminResponse:
        """Update a menu category.

        Args:
            category_id: Category primary key.
            request: Partial update payload.

        Returns:
            MenuCategoryAdminResponse: Updated category row.

        Raises:
            LookupError: If the category does not exist.
            ValueError: If no field is supplied.
        """
        fields = patch_payload(request)
        assignments, params = build_update_statement(
            "category",
            fields,
            {"name", "slug", "display_order"},
        )
        params["category_id"] = category_id
        result = await self.session.execute(
            text(
                f"""
                update menu_categories
                set {assignments}
                where id = :category_id
                returning id, name, slug, display_order
                """
            ),
            params,
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise LookupError(f"Menu category not found: {category_id}")
        self._mark_menu_mutated()
        return self._category_response(row)

    async def upsert_category_translation(
        self,
        category_id: int,
        language_code: str,
        request: MenuCategoryTranslationUpsertRequest,
    ) -> MenuCategoryTranslationResponse:
        """Create or update a category translation.

        Args:
            category_id: Category primary key.
            language_code: Translation language.
            request: Translation payload.

        Returns:
            MenuCategoryTranslationResponse: Upserted translation.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        await self._ensure_category_exists(category_id)
        result = await self.session.execute(
            text(
                """
                insert into menu_category_translations (category_id, language_code, name)
                values (:category_id, :language_code, :name)
                on conflict (category_id, language_code) do update
                set
                    name = excluded.name,
                    updated_at = now()
                returning category_id, language_code, name
                """
            ),
            {"category_id": category_id, "language_code": language_code, **request.model_dump()},
        )
        self._mark_menu_mutated()
        return self._category_translation_response(result.mappings().one())

    async def create_item(self, request: MenuItemCreateRequest) -> MenuItemAdminResponse:
        """Create a menu item.

        Args:
            request: Validated menu item payload.

        Returns:
            MenuItemAdminResponse: Created item row.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        result = await self.session.execute(
            text(
                """
                insert into menu_items (
                    external_id,
                    category_id,
                    name,
                    description,
                    price,
                    tags,
                    is_available,
                    display_order
                )
                values (
                    :external_id,
                    :category_id,
                    :name,
                    :description,
                    :price,
                    :tags,
                    :is_available,
                    :display_order
                )
                returning id, external_id, category_id, name, description, price, tags, is_available, display_order
                """
            ),
            request.model_dump(),
        )
        self._mark_menu_mutated()
        return self._item_response(result.mappings().one())

    async def update_item(self, item_id: int, request: MenuItemUpdateRequest) -> MenuItemAdminResponse:
        """Update a menu item.

        Args:
            item_id: Menu item primary key.
            request: Partial update payload.

        Returns:
            MenuItemAdminResponse: Updated item row.

        Raises:
            LookupError: If the item does not exist.
            ValueError: If no field is supplied.
        """
        fields = patch_payload(request)
        assignments, params = build_update_statement(
            "item",
            fields,
            {
                "category_id",
                "external_id",
                "name",
                "description",
                "price",
                "tags",
                "is_available",
                "display_order",
            },
        )
        params["item_id"] = item_id
        result = await self.session.execute(
            text(
                f"""
                update menu_items
                set {assignments}
                where id = :item_id
                returning id, external_id, category_id, name, description, price, tags, is_available, display_order
                """
            ),
            params,
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise LookupError(f"Menu item not found: {item_id}")
        self._mark_menu_mutated()
        return self._item_response(row)

    async def upsert_item_translation(
        self,
        item_id: int,
        language_code: str,
        request: MenuItemTranslationUpsertRequest,
    ) -> MenuItemTranslationResponse:
        """Create or update a menu item translation.

        Args:
            item_id: Menu item primary key.
            language_code: Translation language.
            request: Translation payload.

        Returns:
            MenuItemTranslationResponse: Upserted translation row.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        await self._ensure_item_exists(item_id)
        result = await self.session.execute(
            text(
                """
                insert into menu_item_translations (menu_item_id, language_code, name, description)
                values (:item_id, :language_code, :name, :description)
                on conflict (menu_item_id, language_code) do update
                set
                    name = excluded.name,
                    description = excluded.description,
                    updated_at = now()
                returning menu_item_id, language_code, name, description
                """
            ),
            {"item_id": item_id, "language_code": language_code, **request.model_dump()},
        )
        self._mark_menu_mutated()
        return self._item_translation_response(result.mappings().one())

    async def list_categories(self) -> MenuCategoryListResponse:
        """List every category with its translations and item count.

        Args:
            None.

        Returns:
            MenuCategoryListResponse: Categories in display order.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the database query fails.
        """
        rows = await self._query_category_details("", {})
        categories = [self._category_detail_response(row) for row in rows]
        return MenuCategoryListResponse(total=len(categories), categories=categories)

    async def get_category(self, category_id: int) -> MenuCategoryAdminDetailResponse:
        """Fetch one category with every stored translation.

        Args:
            category_id: Category primary key.

        Returns:
            MenuCategoryAdminDetailResponse: Category row plus translations.

        Raises:
            LookupError: If the category does not exist.
        """
        rows = await self._query_category_details("where mc.id = :category_id", {"category_id": category_id})
        if not rows:
            raise LookupError(f"Menu category not found: {category_id}")
        return self._category_detail_response(rows[0])

    async def list_items(
        self,
        category_id: int | None = None,
        is_available: bool | None = None,
        search: str | None = None,
    ) -> MenuItemListResponse:
        """List menu items with their translations, filtered for the admin table.

        Args:
            category_id: Restrict to one category, or None for all.
            is_available: Restrict to available/unavailable items, or None for all.
            search: Case-insensitive substring matched against name, description and external id.

        Returns:
            MenuItemListResponse: Items in category then item display order.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if the database query fails.
        """
        filters: list[str] = []
        params: dict[str, Any] = {}
        if category_id is not None:
            filters.append("mi.category_id = :category_id")
            params["category_id"] = category_id
        if is_available is not None:
            filters.append("mi.is_available = :is_available")
            params["is_available"] = is_available
        if search and search.strip():
            # Ένα μόνο bind: το concat_ws αγνοεί το NULL external_id.
            filters.append("concat_ws(' ', mi.name, mi.description, mi.external_id) ilike :search")
            params["search"] = f"%{search.strip()}%"

        rows = await self._query_item_details("where " + " and ".join(filters) if filters else "", params)
        items = [self._item_detail_response(row) for row in rows]
        return MenuItemListResponse(total=len(items), items=items)

    async def get_item(self, item_id: int) -> MenuItemAdminDetailResponse:
        """Fetch one menu item with every stored translation.

        Args:
            item_id: Menu item primary key.

        Returns:
            MenuItemAdminDetailResponse: Item row plus translations.

        Raises:
            LookupError: If the item does not exist.
        """
        rows = await self._query_item_details("where mi.id = :item_id", {"item_id": item_id})
        if not rows:
            raise LookupError(f"Menu item not found: {item_id}")
        return self._item_detail_response(rows[0])

    async def delete_item(self, item_id: int) -> None:
        """Delete a menu item and its translations.

        Args:
            item_id: Menu item primary key.

        Returns:
            None.

        Raises:
            LookupError: If the item does not exist.
        """
        result = await self.session.execute(
            text("delete from menu_items where id = :item_id returning id"),
            {"item_id": item_id},
        )
        if result.scalar_one_or_none() is None:
            raise LookupError(f"Menu item not found: {item_id}")
        self._mark_menu_mutated()

    async def delete_category(self, category_id: int) -> None:
        """Delete an empty menu category and its translations.

        Args:
            category_id: Category primary key.

        Returns:
            None.

        Raises:
            LookupError: If the category does not exist.
            IntegrityError: If the category still has menu items (on delete restrict).
        """
        result = await self.session.execute(
            text("delete from menu_categories where id = :category_id returning id"),
            {"category_id": category_id},
        )
        if result.scalar_one_or_none() is None:
            raise LookupError(f"Menu category not found: {category_id}")
        self._mark_menu_mutated()

    async def reorder_categories(self, category_ids: list[int]) -> int:
        """Rewrite category display order to match the supplied id sequence.

        Args:
            category_ids: Category ids in their new order.

        Returns:
            int: Number of rows updated.

        Raises:
            LookupError: If any id does not exist.
        """
        return await self._reorder("menu_categories", category_ids)

    async def reorder_items(self, item_ids: list[int]) -> int:
        """Rewrite item display order to match the supplied id sequence.

        Args:
            item_ids: Menu item ids in their new order.

        Returns:
            int: Number of rows updated.

        Raises:
            LookupError: If any id does not exist.
        """
        return await self._reorder("menu_items", item_ids)

    async def _reorder(self, table_name: str, ids: list[int]) -> int:
        if table_name not in {"menu_categories", "menu_items"}:
            raise ValueError(f"Unsupported reorder table: {table_name}")

        result = await self.session.execute(
            text(
                f"""
                update {table_name} as target
                set display_order = ordered.position
                from (
                    select id, position
                    from unnest(cast(:ids as int[])) with ordinality as t(id, position)
                ) as ordered
                where target.id = ordered.id
                returning target.id
                """
            ),
            {"ids": ids},
        )
        updated = len(result.scalars().all())
        if updated != len(ids):
            raise LookupError(f"Unknown {table_name} ids in reorder request")
        self._mark_menu_mutated()
        return updated

    async def _query_category_details(self, where_clause: str, params: dict[str, Any]) -> list[RowMapping]:
        result = await self.session.execute(
            text(
                f"""
                select
                    mc.id,
                    mc.name,
                    mc.slug,
                    mc.display_order,
                    (select count(*) from menu_items mi where mi.category_id = mc.id) as item_count,
                    jsonb_object_agg(mct.language_code, mct.name)
                        filter (where mct.language_code is not null) as translations
                from menu_categories mc
                left join menu_category_translations mct on mct.category_id = mc.id
                {where_clause}
                group by mc.id, mc.name, mc.slug, mc.display_order
                order by mc.display_order asc, mc.id asc
                """
            ),
            params,
        )
        return list(result.mappings().all())

    async def _query_item_details(self, where_clause: str, params: dict[str, Any]) -> list[RowMapping]:
        result = await self.session.execute(
            text(
                f"""
                select
                    mi.id,
                    mi.external_id,
                    mi.category_id,
                    mc.name as category_name,
                    mi.name,
                    mi.description,
                    mi.price,
                    mi.tags,
                    mi.is_available,
                    mi.display_order,
                    jsonb_object_agg(
                        mit.language_code,
                        jsonb_build_object('name', mit.name, 'description', mit.description)
                    ) filter (where mit.language_code is not null) as translations
                from menu_items mi
                join menu_categories mc on mc.id = mi.category_id
                left join menu_item_translations mit on mit.menu_item_id = mi.id
                {where_clause}
                group by mi.id, mc.name, mc.display_order
                order by mc.display_order asc, mi.display_order asc, mi.id asc
                """
            ),
            params,
        )
        return list(result.mappings().all())

    async def _ensure_category_exists(self, category_id: int) -> None:
        result = await self.session.execute(
            text("select 1 from menu_categories where id = :category_id"),
            {"category_id": category_id},
        )
        if result.scalar_one_or_none() is None:
            raise LookupError(f"Menu category not found: {category_id}")

    async def _ensure_item_exists(self, item_id: int) -> None:
        result = await self.session.execute(
            text("select 1 from menu_items where id = :item_id"),
            {"item_id": item_id},
        )
        if result.scalar_one_or_none() is None:
            raise LookupError(f"Menu item not found: {item_id}")

    @staticmethod
    def _category_response(row: RowMapping) -> MenuCategoryAdminResponse:
        return MenuCategoryAdminResponse(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            display_order=row["display_order"],
        )

    @staticmethod
    def _category_translation_response(row: RowMapping) -> MenuCategoryTranslationResponse:
        return MenuCategoryTranslationResponse(
            category_id=row["category_id"],
            language_code=row["language_code"],
            name=row["name"],
        )

    @staticmethod
    def _item_response(row: RowMapping) -> MenuItemAdminResponse:
        return MenuItemAdminResponse(
            id=row["id"],
            external_id=row["external_id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=float(row["price"]),
            tags=list(row["tags"] or []),
            is_available=row["is_available"],
            display_order=row["display_order"],
        )

    @staticmethod
    def _item_translation_response(row: RowMapping) -> MenuItemTranslationResponse:
        return MenuItemTranslationResponse(
            menu_item_id=row["menu_item_id"],
            language_code=row["language_code"],
            name=row["name"],
            description=row["description"],
        )

    @staticmethod
    def _category_detail_response(row: RowMapping) -> MenuCategoryAdminDetailResponse:
        translations = decode_jsonb_object(row["translations"])
        return MenuCategoryAdminDetailResponse(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            display_order=row["display_order"],
            item_count=row["item_count"],
            translations={code: str(name) for code, name in translations.items()},
        )

    @staticmethod
    def _item_detail_response(row: RowMapping) -> MenuItemAdminDetailResponse:
        translations = decode_jsonb_object(row["translations"])
        return MenuItemAdminDetailResponse(
            id=row["id"],
            external_id=row["external_id"],
            category_id=row["category_id"],
            category_name=row["category_name"],
            name=row["name"],
            description=row["description"],
            price=float(row["price"]),
            tags=list(row["tags"] or []),
            is_available=row["is_available"],
            display_order=row["display_order"],
            translations={
                code: MenuItemTranslationValue(
                    name=str(value.get("name", "")),
                    description=str(value.get("description", "")),
                )
                for code, value in translations.items()
                if isinstance(value, dict)
            },
        )
