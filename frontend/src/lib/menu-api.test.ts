import { describe, expect, it } from "vitest";
import {
  mapMenuCategories,
  type ApiMenuCategory,
  type ApiMenuItem,
} from "@/lib/menu-api";

function item(id: string, categoryName: string): ApiMenuItem {
  return {
    external_id: id,
    name: `Item ${id}`,
    category_name: categoryName,
    price: 10,
    tags: [],
  };
}

function category(
  slug: string,
  name: string,
  displayOrder: number,
): ApiMenuCategory {
  return {
    slug,
    name,
    display_order: displayOrder,
    items: [item(slug, name)],
  };
}

describe("mapMenuCategories", () => {
  it("groups raw sushi categories under one stable navigation id", () => {
    const groups = mapMenuCategories([
      category("uramaki-hossomaki-6pcs", "Uramaki / Hossomaki (6pcs)", 10),
      category("nigiri-2pcs", "Nigiri (2pcs)", 20),
      category("signature-rolls-8pcs", "Signature Rolls (8pcs)", 30),
    ]);

    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({ id: "sushi", label: "Sushi" });
    expect(groups[0].sections.map((section) => section.category)).toEqual([
      "Uramaki / Hossomaki (6pcs)",
      "Nigiri (2pcs)",
      "Signature Rolls (8pcs)",
    ]);
  });

  it("keeps the same group id while preserving localized section labels", () => {
    const russian = mapMenuCategories([
      category("raw", "Сырые блюда", 40),
      category("crispy-fried-rolls-6pcs", "Хрустящие жареные роллы (6 шт.)", 50),
    ]);
    const german = mapMenuCategories([
      category("raw", "Rohe Gerichte", 40),
      category("crispy-fried-rolls-6pcs", "Knusprige frittierte Rollen (6 Stk.)", 50),
    ]);

    expect(russian[0].id).toBe("sushi");
    expect(german[0].id).toBe("sushi");
    expect(russian[0].sections[0].category).toBe("Сырые блюда");
    expect(german[0].sections[0].category).toBe("Rohe Gerichte");
  });

  it("maps the complete production category taxonomy to twelve navigation groups", () => {
    const productionSlugs = [
      "uramaki-hossomaki-6pcs",
      "nigiri-2pcs",
      "signature-rolls-8pcs",
      "raw",
      "crispy-fried-rolls-6pcs",
      "bites",
      "bao-buns-2pcs",
      "noodles",
      "burger-sando-served-with-fries",
      "poke-bowl",
      "salads",
      "desserts",
      "masao-cocktails",
      "classic-cocktails",
      "mocktails",
      "soft-drinks",
      "ciders",
      "beers",
      "whiskey",
      "white-wines",
      "rose-wines",
      "red-wines",
      "champagne-sparkling",
      "shisha",
    ];

    const groups = mapMenuCategories(
      productionSlugs.map((slug, index) => category(slug, `Category ${index}`, index * 10)),
    );

    expect(groups.map((group) => group.id)).toEqual([
      "sushi",
      "bites",
      "bao",
      "noodles",
      "burgers",
      "poke",
      "salads",
      "desserts",
      "cocktails",
      "drinks",
      "wines",
      "shisha",
    ]);
    expect(groups.map((group) => group.sections.length)).toEqual([
      5, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 1,
    ]);
  });

  it("preserves unknown API categories after the configured navigation groups", () => {
    const groups = mapMenuCategories([
      category("seasonal-specials", "Saisonale Spezialitäten", 5),
      category("noodles", "Nudeln", 80),
    ]);

    expect(groups.map((group) => group.id)).toEqual(["noodles", "seasonal-specials"]);
    expect(groups[1].label).toBe("Saisonale Spezialitäten");
  });
});
