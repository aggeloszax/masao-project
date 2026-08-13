from __future__ import annotations

"""Canonical allergen registry for allergy alerts.

Οι κωδικοί ακολουθούν τα 14 αλλεργιογόνα της ΕΕ (Annex II, Reg. 1169/2011)
ώστε το matching πελάτη-πιάτου να είναι ντετερμινιστικό: ελεύθερο κείμενο
δεν συγκρίνεται ποτέ με ελεύθερο κείμενο.
"""

# Η σειρά καθορίζει την εμφάνιση στο frontend picker.
ALLERGEN_CODES: tuple[str, ...] = (
    "gluten",
    "crustaceans",
    "eggs",
    "fish",
    "peanuts",
    "soybeans",
    "milk",
    "nuts",
    "celery",
    "mustard",
    "sesame",
    "sulphites",
    "lupin",
    "molluscs",
)

ALLERGEN_CODE_SET: frozenset[str] = frozenset(ALLERGEN_CODES)

# Θέση κάθε κωδικού στην κανονική σειρά, για γρήγορο sort μικρών συνόλων.
ALLERGEN_RANK: dict[str, int] = {code: rank for rank, code in enumerate(ALLERGEN_CODES)}

# Localized labels ανά γλώσσα του app (ίδια σειρά γλωσσών με LanguageCode).
ALLERGEN_LABELS: dict[str, dict[str, str]] = {
    "el": {
        "gluten": "Γλουτένη (σιτηρά)",
        "crustaceans": "Καρκινοειδή (γαρίδα, καβούρι)",
        "eggs": "Αυγά",
        "fish": "Ψάρι",
        "peanuts": "Αράπικα φιστίκια",
        "soybeans": "Σόγια",
        "milk": "Γάλα (λακτόζη)",
        "nuts": "Ξηροί καρποί",
        "celery": "Σέλινο",
        "mustard": "Μουστάρδα",
        "sesame": "Σουσάμι",
        "sulphites": "Θειώδη",
        "lupin": "Λούπινο",
        "molluscs": "Μαλάκια",
    },
    "en": {
        "gluten": "Gluten (cereals)",
        "crustaceans": "Crustaceans (shrimp, crab)",
        "eggs": "Eggs",
        "fish": "Fish",
        "peanuts": "Peanuts",
        "soybeans": "Soybeans",
        "milk": "Milk (lactose)",
        "nuts": "Tree nuts",
        "celery": "Celery",
        "mustard": "Mustard",
        "sesame": "Sesame",
        "sulphites": "Sulphites",
        "lupin": "Lupin",
        "molluscs": "Molluscs",
    },
    "de": {
        "gluten": "Gluten (Getreide)",
        "crustaceans": "Krebstiere (Garnelen, Krabben)",
        "eggs": "Eier",
        "fish": "Fisch",
        "peanuts": "Erdnüsse",
        "soybeans": "Soja",
        "milk": "Milch (Laktose)",
        "nuts": "Schalenfrüchte",
        "celery": "Sellerie",
        "mustard": "Senf",
        "sesame": "Sesam",
        "sulphites": "Sulfite",
        "lupin": "Lupinen",
        "molluscs": "Weichtiere",
    },
    "it": {
        "gluten": "Glutine (cereali)",
        "crustaceans": "Crostacei (gamberi, granchio)",
        "eggs": "Uova",
        "fish": "Pesce",
        "peanuts": "Arachidi",
        "soybeans": "Soia",
        "milk": "Latte (lattosio)",
        "nuts": "Frutta a guscio",
        "celery": "Sedano",
        "mustard": "Senape",
        "sesame": "Sesamo",
        "sulphites": "Solfiti",
        "lupin": "Lupini",
        "molluscs": "Molluschi",
    },
    "sv": {
        "gluten": "Gluten (spannmål)",
        "crustaceans": "Kräftdjur (räkor, krabba)",
        "eggs": "Ägg",
        "fish": "Fisk",
        "peanuts": "Jordnötter",
        "soybeans": "Soja",
        "milk": "Mjölk (laktos)",
        "nuts": "Nötter",
        "celery": "Selleri",
        "mustard": "Senap",
        "sesame": "Sesamfrön",
        "sulphites": "Sulfiter",
        "lupin": "Lupin",
        "molluscs": "Blötdjur",
    },
    "fr": {
        "gluten": "Gluten (céréales)", "crustaceans": "Crustacés (crevettes, crabe)",
        "eggs": "Œufs", "fish": "Poisson", "peanuts": "Arachides", "soybeans": "Soja",
        "milk": "Lait (lactose)", "nuts": "Fruits à coque", "celery": "Céleri",
        "mustard": "Moutarde", "sesame": "Sésame", "sulphites": "Sulfites",
        "lupin": "Lupin", "molluscs": "Mollusques",
    },
    "ru": {
        "gluten": "Глютен (злаки)", "crustaceans": "Ракообразные (креветки, краб)",
        "eggs": "Яйца", "fish": "Рыба", "peanuts": "Арахис", "soybeans": "Соя",
        "milk": "Молоко (лактоза)", "nuts": "Орехи", "celery": "Сельдерей",
        "mustard": "Горчица", "sesame": "Кунжут", "sulphites": "Сульфиты",
        "lupin": "Люпин", "molluscs": "Моллюски",
    },
    "he": {
        "gluten": "גלוטן (דגנים)",
        "crustaceans": "סרטנאים (שרימפס, סרטן)",
        "eggs": "ביצים",
        "fish": "דג",
        "peanuts": "בוטנים",
        "soybeans": "סויה",
        "milk": "חלב (לקטוז)",
        "nuts": "אגוזים",
        "celery": "סלרי",
        "mustard": "חרדל",
        "sesame": "שומשום",
        "sulphites": "סולפיטים",
        "lupin": "תורמוס",
        "molluscs": "רכיכות",
    },
    "tr": {
        "gluten": "Gluten (tahıllar)",
        "crustaceans": "Kabuklular (karides, yengeç)",
        "eggs": "Yumurta",
        "fish": "Balık",
        "peanuts": "Yer fıstığı",
        "soybeans": "Soya",
        "milk": "Süt (laktoz)",
        "nuts": "Sert kabuklu meyveler",
        "celery": "Kereviz",
        "mustard": "Hardal",
        "sesame": "Susam",
        "sulphites": "Sülfitler",
        "lupin": "Acı bakla (lüpen)",
        "molluscs": "Yumuşakçalar",
    },
}


def to_canonical_order(codes: set[str]) -> list[str]:
    """Order known allergen codes canonically, dropping unknown ones.

    Args:
        codes: Allergen codes from any source (request, database, matching).

    Returns:
        list[str]: Known codes in ALLERGEN_CODES registry order.

    Raises:
        None.
    """
    return sorted(codes & ALLERGEN_CODE_SET, key=ALLERGEN_RANK.__getitem__)


def normalize_allergens(values: list[str]) -> list[str]:
    """Normalize raw allergen codes to unique canonical codes.

    Args:
        values: Raw allergen codes from a request or the database.

    Returns:
        list[str]: Deduplicated lowercase codes in canonical registry order.

    Raises:
        ValueError: If a code is not one of the 14 canonical allergens.
    """
    cleaned = {value.strip().lower() for value in values if value.strip()}
    unknown = cleaned - ALLERGEN_CODE_SET
    if unknown:
        raise ValueError(f"Unknown allergen codes: {', '.join(sorted(unknown))}")
    return to_canonical_order(cleaned)


def match_allergens(item_allergens: list[str], customer_allergens: set[str]) -> list[str]:
    """Return the customer's declared allergens found in a menu item.

    Args:
        item_allergens: Canonical allergen codes declared on the menu item.
        customer_allergens: Canonical allergen codes declared by the guest.

    Returns:
        list[str]: Intersection in canonical registry order. Empty when the
            guest declared nothing or the item is not flagged.

    Raises:
        None.
    """
    if not customer_allergens:
        return []
    return to_canonical_order(set(item_allergens) & customer_allergens)


def allergen_labels(language_code: str) -> dict[str, str]:
    """Return localized allergen labels, falling back to Greek.

    Args:
        language_code: Guest language code.

    Returns:
        dict[str, str]: Mapping of canonical code to display label.

    Raises:
        None.
    """
    return ALLERGEN_LABELS.get(language_code, ALLERGEN_LABELS["el"])


def format_allergen_names(codes: list[str], language_code: str) -> str:
    """Format allergen codes as a human-readable localized list.

    Args:
        codes: Canonical allergen codes.
        language_code: Guest language code.

    Returns:
        str: Comma-separated localized labels (e.g. "Ψάρι, Σουσάμι").

    Raises:
        None.
    """
    labels = allergen_labels(language_code)
    return ", ".join(labels.get(code, code) for code in codes)
