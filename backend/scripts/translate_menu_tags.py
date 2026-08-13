from __future__ import annotations

import asyncio
import json
from pathlib import Path

from anthropic import AsyncAnthropic

from api.config import settings


ROOT = Path(__file__).resolve().parents[2]
MENU_PATH = ROOT / "frontend" / "src" / "data" / "menu-mock.json"
OUTPUT_PATH = ROOT / "frontend" / "src" / "data" / "tag-translations-fr-ru.json"


async def main() -> None:
    items = json.loads(MENU_PATH.read_text(encoding="utf-8"))
    tags = sorted({tag for item in items for tag in item["tags"]})
    prompt = f"""
Translate these restaurant menu characteristic tags into natural French and Russian.
Return ONLY a valid JSON object keyed by the exact original tag. Each value must be
an object with exactly the keys fr and ru. Preserve culinary loanwords and brand-like
terms where appropriate. Translate characteristics such as light, refreshing, spicy,
sweet, dry, vegan-friendly and similar terms naturally. Do not omit or rename keys.

Tags:
{json.dumps(tags, ensure_ascii=False)}
""".strip()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    text_value = "".join(block.text for block in response.content if block.type == "text")
    start, end = text_value.find("{"), text_value.rfind("}")
    translated = json.loads(text_value[start : end + 1])
    if set(translated) != set(tags):
        raise ValueError("Translated tag keys do not match the menu tags")
    for tag, values in translated.items():
        if set(values) != {"fr", "ru"} or not all(str(value).strip() for value in values.values()):
            raise ValueError(f"Incomplete tag translation: {tag}")
    OUTPUT_PATH.write_text(
        json.dumps(translated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(translated)} tag translations")


if __name__ == "__main__":
    asyncio.run(main())
