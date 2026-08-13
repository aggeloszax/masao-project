from __future__ import annotations

import asyncio
import json
from pathlib import Path

from anthropic import AsyncAnthropic

from api.config import settings


ROOT = Path(__file__).resolve().parents[2]
MENU_PATH = ROOT / "frontend" / "src" / "data" / "menu-mock.json"
LANGUAGES = {"fr": "French", "ru": "Russian"}
BATCH_SIZE = 20


def extract_json(text: str) -> list[dict[str, str]]:
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        raise ValueError("Translator did not return a JSON array")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, list):
        raise ValueError("Translator response is not a list")
    return value


async def translate_batch(
    client: AsyncAnthropic,
    items: list[dict[str, object]],
    language_code: str,
    language_name: str,
) -> dict[str, dict[str, str]]:
    source = [
        {
            "id": item["id"],
            "name": item["translations"]["en"]["name"],
            "description": item["translations"]["en"]["description"],
            "category": item["translations"]["en"]["category"],
        }
        for item in items
    ]
    prompt = f"""
Translate this restaurant menu data from English into natural {language_name}.
Return ONLY a valid JSON array with the exact keys id, name, description, category.
Keep every id unchanged. Preserve brand names, cocktail names, Japanese dish names,
numbers, units and ingredient accuracy. Translate generic food terms and category
labels naturally. Use the same translation for every repeated category. Do not add
explanations, ingredients or marketing claims.

Input JSON:
{json.dumps(source, ensure_ascii=False)}
""".strip()
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=12000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    rows = extract_json(text)
    translated: dict[str, dict[str, str]] = {}
    expected_ids = {str(item["id"]) for item in items}
    for row in rows:
        item_id = str(row.get("id", ""))
        if item_id not in expected_ids:
            raise ValueError(f"Unexpected translated item id: {item_id}")
        values = {key: str(row.get(key, "")).strip() for key in ("name", "description", "category")}
        if not all(values.values()):
            raise ValueError(f"Incomplete {language_code} translation for {item_id}")
        translated[item_id] = values
    if set(translated) != expected_ids:
        missing = sorted(expected_ids - set(translated))
        raise ValueError(f"Missing {language_code} translations: {missing}")
    return translated


async def main() -> None:
    items = json.loads(MENU_PATH.read_text(encoding="utf-8"))
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    completed: dict[str, dict[str, dict[str, str]]] = {}

    for language_code, language_name in LANGUAGES.items():
        language_rows: dict[str, dict[str, str]] = {}
        for start in range(0, len(items), BATCH_SIZE):
            batch = items[start : start + BATCH_SIZE]
            language_rows.update(
                await translate_batch(client, batch, language_code, language_name)
            )
            print(f"{language_code}: {min(start + BATCH_SIZE, len(items))}/{len(items)}")
        completed[language_code] = language_rows

    for item in items:
        item_id = str(item["id"])
        for language_code in LANGUAGES:
            item["translations"][language_code] = completed[language_code][item_id]

    MENU_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {MENU_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
