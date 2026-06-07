import pytest

from api.services.admin_menu_service import build_update_statement


def test_build_update_statement_uses_only_supplied_fields() -> None:
    set_clause, params = build_update_statement(
        "item",
        {"price": 12.5, "is_available": False},
        {"price", "is_available"},
    )

    assert set_clause == "price = :price, is_available = :is_available"
    assert params == {"price": 12.5, "is_available": False}


def test_build_update_statement_rejects_empty_fields() -> None:
    with pytest.raises(ValueError):
        build_update_statement("item", {}, {"price"})


def test_build_update_statement_rejects_unsupported_fields() -> None:
    with pytest.raises(ValueError):
        build_update_statement("item", {"unsafe": "value"}, {"price"})
