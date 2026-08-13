from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from database import engine


ROOT = Path(__file__).resolve().parents[2]
MENU_PATH = ROOT / "frontend" / "src" / "data" / "menu-mock.json"
LANGUAGES = ("en", "de", "it", "sv", "fr", "ru", "he")


async def main() -> None:
    items = json.loads(MENU_PATH.read_text(encoding="utf-8"))
    category_rows: dict[tuple[str, str], dict[str, str]] = {}
    item_rows: list[dict[str, str]] = []
    for item in items:
        base_category = item["category"]
        for language_code in LANGUAGES:
            translated = item["translations"][language_code]
            category_rows[(base_category, language_code)] = {
                "category_name": base_category,
                "language_code": language_code,
                "name": translated["category"],
            }
            item_rows.append(
                {
                    "external_id": item["id"],
                    "language_code": language_code,
                    "name": translated["name"],
                    "description": translated["description"],
                }
            )

    async with engine.begin() as connection:
        await connection.execute(text("alter table menu_category_translations drop constraint if exists ck_menu_category_translations_language"))
        await connection.execute(text("alter table menu_category_translations add constraint ck_menu_category_translations_language check (language_code in ('el', 'en', 'de', 'it', 'sv', 'fr', 'ru', 'he'))"))
        await connection.execute(text("alter table menu_item_translations drop constraint if exists ck_menu_item_translations_language"))
        await connection.execute(text("alter table menu_item_translations add constraint ck_menu_item_translations_language check (language_code in ('el', 'en', 'de', 'it', 'sv', 'fr', 'ru', 'he'))"))
        await connection.execute(
            text("""
                insert into menu_category_translations (category_id, language_code, name)
                select c.id, :language_code, :name from menu_categories c where c.name = :category_name
                on conflict (category_id, language_code) do update set name = excluded.name, updated_at = now()
            """),
            list(category_rows.values()),
        )
        await connection.execute(
            text("""
                insert into menu_item_translations (menu_item_id, language_code, name, description)
                select mi.id, :language_code, :name, :description from menu_items mi where mi.external_id = :external_id
                on conflict (menu_item_id, language_code) do update set name = excluded.name, description = excluded.description, updated_at = now()
            """),
            item_rows,
        )
    await engine.dispose()
    print(f"Applied {len(category_rows)} category and {len(item_rows)} item translations")


if __name__ == "__main__":
    asyncio.run(main())
