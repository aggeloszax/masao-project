import re
from pathlib import Path

import pytest

from api.schemas.menu import LanguageCode
from api.services.allergens import (
    ALLERGEN_CODES,
    ALLERGEN_LABELS,
    allergen_labels,
    format_allergen_names,
    match_allergens,
    normalize_allergens,
    to_canonical_order,
)


def test_registry_has_14_eu_allergens() -> None:
    assert len(ALLERGEN_CODES) == 14
    assert len(set(ALLERGEN_CODES)) == 14


def test_registry_labels_cover_every_language_and_code() -> None:
    supported_languages = set(LanguageCode.__args__)

    assert set(ALLERGEN_LABELS) == supported_languages
    for language_code, labels in ALLERGEN_LABELS.items():
        assert set(labels) == set(ALLERGEN_CODES), f"missing labels for {language_code}"


def test_normalize_allergens_dedupes_and_orders_canonically() -> None:
    result = normalize_allergens(["FISH", " gluten ", "fish"])

    assert result == ["gluten", "fish"]


def test_normalize_allergens_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError, match="Unknown allergen codes"):
        normalize_allergens(["fish", "kryptonite"])


def test_match_allergens_returns_intersection_in_canonical_order() -> None:
    matched = match_allergens(["sesame", "fish", "gluten"], {"fish", "sesame", "milk"})

    assert matched == ["fish", "sesame"]


def test_match_allergens_empty_when_customer_declared_nothing() -> None:
    assert match_allergens(["fish"], set()) == []


def test_allergen_labels_falls_back_to_greek() -> None:
    assert allergen_labels("xx") == ALLERGEN_LABELS["el"]


def test_format_allergen_names_localizes_labels() -> None:
    assert format_allergen_names(["fish", "sesame"], "el") == "Ψάρι, Σουσάμι"
    assert format_allergen_names(["fish", "sesame"], "en") == "Fish, Sesame"


def test_to_canonical_order_drops_unknown_codes() -> None:
    assert to_canonical_order({"sesame", "kryptonite", "gluten"}) == ["gluten", "sesame"]


def test_sql_check_constraints_match_python_registry() -> None:
    # Guard κατά του drift: οι 2 CHECK constraints του migration πρέπει να
    # απαριθμούν ακριβώς τους ίδιους κωδικούς με το Python registry, αλλιώς
    # ένας νέος κωδικός θα περνούσε το Pydantic και θα έσκαγε ως 500 στη βάση.
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "004_add_allergens.sql"
    sql = sql_path.read_text(encoding="utf-8")

    constraint_arrays = re.findall(r"allergens <@ array\[(.*?)\]::text\[\]", sql, flags=re.DOTALL)

    assert len(constraint_arrays) == 2
    for block in constraint_arrays:
        codes = re.findall(r"'([a-z]+)'", block)
        assert codes == list(ALLERGEN_CODES)
