from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MENU_JSON = ROOT / "frontend" / "src" / "data" / "menu-mock.json"
OUTPUT_SQL = ROOT / "backend" / "sql" / "002_seed_full_menu_from_frontend.sql"
LANGUAGES = ("el", "en", "de", "it", "sv", "he")


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or re.sub(r"\W+", "-", value.lower(), flags=re.UNICODE).strip("-")


def split_description(description: str) -> tuple[str, str]:
    parts = [part.strip() for part in description.split("|", maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    return description.strip(), description.strip()


def category_rows(menu: list[dict[str, Any]]) -> list[tuple[str, str, int]]:
    seen: dict[str, tuple[str, str, int]] = {}
    for item in menu:
        category = item["category"].strip()
        if category not in seen:
            seen[category] = (category, slugify(category), (len(seen) + 1) * 10)
    return list(seen.values())


def category_translation_rows(menu: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    translations: dict[tuple[str, str], str] = {}
    for item in menu:
        category = item["category"].strip()
        translations.setdefault((category, "el"), category)
        for lang, data in item["translations"].items():
            if lang in LANGUAGES:
                translations.setdefault((category, lang), data["category"].strip())
    return [(category, lang, name) for (category, lang), name in sorted(translations.items())]


def menu_item_rows(menu: list[dict[str, Any]]) -> list[tuple[str, str, str, str, float, list[str], int]]:
    rows: list[tuple[str, str, str, str, float, list[str], int]] = []
    for index, item in enumerate(menu, start=1):
        _el_description, en_description = split_description(item["description"])
        canonical_description = item["translations"].get("en", {}).get("description", en_description).strip()
        rows.append(
            (
                item["id"].strip(),
                item["category"].strip(),
                item["name"].strip(),
                canonical_description,
                float(item["price"]),
                [str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()],
                index,
            )
        )
    return rows


def item_translation_rows(menu: list[dict[str, Any]]) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for item in menu:
        el_description, _en_description = split_description(item["description"])
        rows.append((item["id"].strip(), "el", item["name"].strip(), el_description))
        for lang, data in item["translations"].items():
            if lang in LANGUAGES:
                rows.append(
                    (
                        item["id"].strip(),
                        lang,
                        data["name"].strip(),
                        data["description"].strip(),
                    )
                )
    return rows


def values_block(rows: list[tuple[Any, ...]]) -> str:
    rendered_rows: list[str] = []
    for row in rows:
        rendered_values: list[str] = []
        for value in row:
            if isinstance(value, str):
                rendered_values.append(sql_quote(value))
            elif isinstance(value, list):
                rendered_values.append("array[" + ", ".join(sql_quote(str(item)) for item in value) + "]::text[]")
            elif isinstance(value, float):
                rendered_values.append(f"{value:.2f}")
            else:
                rendered_values.append(str(value))
        rendered_rows.append("    (" + ", ".join(rendered_values) + ")")
    return ",\n".join(rendered_rows)


def build_sql(menu: list[dict[str, Any]]) -> str:
    categories = category_rows(menu)
    category_translations = category_translation_rows(menu)
    items = menu_item_rows(menu)
    item_translations = item_translation_rows(menu)

    return f"""-- Generated from frontend/src/data/menu-mock.json.
-- Do not edit rows manually; update the JSON source or the generator script.

begin;

insert into menu_categories (name, slug, display_order)
values
{values_block(categories)}
on conflict (name) do update
set
    slug = excluded.slug,
    display_order = excluded.display_order;

insert into menu_category_translations (category_id, language_code, name)
select c.id, v.language_code, v.name
from (
    values
{values_block(category_translations)}
) as v(category_name, language_code, name)
join menu_categories c on c.name = v.category_name
on conflict (category_id, language_code) do update
set
    name = excluded.name,
    updated_at = now();

insert into menu_items (external_id, category_id, name, description, price, tags, is_available, display_order)
select v.external_id, c.id, v.name, v.description, v.price, v.tags, true, v.display_order
from (
    values
{values_block(items)}
) as v(external_id, category_name, name, description, price, tags, display_order)
join menu_categories c on c.name = v.category_name
on conflict (external_id) where external_id is not null do update
set
    category_id = excluded.category_id,
    name = excluded.name,
    description = excluded.description,
    price = excluded.price,
    tags = excluded.tags,
    is_available = excluded.is_available,
    display_order = excluded.display_order;

insert into menu_item_translations (menu_item_id, language_code, name, description)
select mi.id, v.language_code, v.name, v.description
from (
    values
{values_block(item_translations)}
) as v(external_id, language_code, name, description)
join menu_items mi on mi.external_id = v.external_id
on conflict (menu_item_id, language_code) do update
set
    name = excluded.name,
    description = excluded.description,
    updated_at = now();

commit;
"""


def main() -> None:
    menu = json.loads(MENU_JSON.read_text(encoding="utf-8"))
    OUTPUT_SQL.write_text(build_sql(menu), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT_SQL}")
    print(f"Items: {len(menu)}")
    print(f"Categories: {len(category_rows(menu))}")
    print(f"Item translations: {len(item_translation_rows(menu))}")


if __name__ == "__main__":
    main()
