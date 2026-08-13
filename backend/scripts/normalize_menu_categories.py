from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MENU_PATH = ROOT / "frontend" / "src" / "data" / "menu-mock.json"
LANGUAGES = ("en", "de", "it", "sv", "fr", "ru", "he")

PRESERVED_CATEGORIES = {
    "Uramaki / Hossomaki (6pcs)",
    "Nigiri (2pcs)",
    "Signature Rolls (8pcs)",
    "Crispy Fried Rolls (6pcs)",
    "Bao Buns (2pcs)",
    "Burger & Sando (served with fries)",
    "Poke Bowl",
    "Masao Cocktails",
}

OVERRIDES = {
    "Signature Rolls (8pcs)": {
        "fr": "Rolls Signature (8 pièces)",
        "ru": "Авторские роллы (8 шт.)",
    },
    "Bao Buns (2pcs)": {
        "fr": "Bao Buns (2 pièces)",
        "ru": "Булочки бао (2 шт.)",
    },
}


def main() -> None:
    items = json.loads(MENU_PATH.read_text(encoding="utf-8"))
    canonical: dict[str, dict[str, str]] = {}
    for item in items:
        english = item["translations"]["en"]["category"]
        canonical.setdefault(
            english,
            {language: item["translations"][language]["category"] for language in LANGUAGES},
        )
    for english, translated in OVERRIDES.items():
        canonical[english] = translated
    for item in items:
        english = item["translations"]["en"]["category"]
        official_category = item["category"]
        official_name = item["name"]
        for language in LANGUAGES:
            item["translations"][language]["name"] = official_name
            item["translations"][language]["category"] = (
                official_category
                if official_category in PRESERVED_CATEGORIES
                else canonical[english][language]
            )
    MENU_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
