from api.services.menu_service import MenuItemRecord, group_menu_items


def _record(
    item_id: int,
    category_id: int,
    category_name: str,
    category_display_order: int,
    item_name: str,
    item_display_order: int,
    is_available: bool = True,
) -> MenuItemRecord:
    return MenuItemRecord(
        id=item_id,
        external_id=f"TEST{item_id:03d}",
        category_id=category_id,
        category_slug=category_name.lower().replace(" ", "-"),
        category_name=category_name,
        category_display_order=category_display_order,
        name=item_name,
        description=f"{item_name} description",
        price=10.0,
        tags=["test"],
        is_available=is_available,
        display_order=item_display_order,
        language_code="en",
    )


def test_group_menu_items_groups_by_category() -> None:
    items = [
        _record(1, 10, "Sushi", 1, "Salmon Roll", 1),
        _record(2, 10, "Sushi", 1, "Tuna Roll", 2),
        _record(3, 20, "Desserts", 2, "Tiramisu", 1),
    ]

    categories = group_menu_items(items)

    assert [category.name for category in categories] == ["Sushi", "Desserts"]
    assert [item.name for item in categories[0].items] == ["Salmon Roll", "Tuna Roll"]


def test_group_menu_items_skips_unavailable_by_default() -> None:
    items = [
        _record(1, 10, "Sushi", 1, "Available Roll", 1),
        _record(2, 10, "Sushi", 1, "Unavailable Roll", 2, is_available=False),
    ]

    categories = group_menu_items(items)

    assert len(categories[0].items) == 1
    assert categories[0].items[0].name == "Available Roll"


def test_group_menu_items_can_include_unavailable_items() -> None:
    items = [
        _record(1, 10, "Sushi", 1, "Available Roll", 1),
        _record(2, 10, "Sushi", 1, "Unavailable Roll", 2, is_available=False),
    ]

    categories = group_menu_items(items, include_unavailable=True)

    assert [item.name for item in categories[0].items] == ["Available Roll", "Unavailable Roll"]
