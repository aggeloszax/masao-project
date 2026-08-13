from __future__ import annotations

from typing import Any

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

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
