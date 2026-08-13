import menuMock from "./menu-mock.json";
import type { Lang } from "@/i18n/config";

/** Per-language overrides present on every item (all langs except the Greek base). */
export type Translation = { name: string; description: string; category: string };

export type MenuItem = {
  id: string;
  name: string;
  price: number;
  description: string;
  category: string;
  tags: string[];
  translations: Partial<Record<Exclude<Lang, "el">, Translation>>;
};

export const menu: MenuItem[] = menuMock;

/**
 * Resolve an item's display fields for a language. Greek (`el`) is the base
 * record: name + the Greek half of `description` + the base category. Other
 * languages come from `translations`, falling back to the base if missing.
 */
export function getLocalized(item: MenuItem, lang: Lang): Translation {
  if (lang === "el") {
    return {
      name: item.name,
      description: splitDescription(item.description).primary,
      category: item.category,
    };
  }
  const t = item.translations[lang] ?? ((lang === "fr" || lang === "ru") ? item.translations.en : undefined);
  return {
    name: t?.name ?? item.name,
    description: t?.description ?? splitDescription(item.description).primary,
    category: t?.category ?? item.category,
  };
}

/**
 * Descriptions are stored as "Greek | English". Favour Greek as the primary
 * line and surface English as an elegant muted subtitle. Single-language
 * descriptions (drinks, wines, shisha) fall through as the primary line only.
 */
export function splitDescription(description: string): {
  primary: string;
  secondary?: string;
} {
  const [primary, secondary] = description.split("|").map((s) => s.trim());
  return secondary ? { primary, secondary } : { primary };
}

/**
 * High-level lounge sections. Each maps one or more raw menu categories so the
 * sticky nav stays short (Sushi, Bao, Cocktails, Shisha…) while preserving the
 * original sub-category headers inside.
 */
const GROUP_DEFS: { id: string; label: string; categories: string[] }[] = [
  {
    id: "sushi",
    label: "Sushi",
    categories: [
      "Uramaki / Hossomaki (6pcs)",
      "Nigiri (2pcs)",
      "Signature Rolls (8pcs)",
      "Raw",
      "Crispy Fried Rolls (6pcs)",
    ],
  },
  { id: "bites", label: "Bites", categories: ["Bites"] },
  { id: "bao", label: "Bao", categories: ["Bao Buns (2pcs)"] },
  { id: "noodles", label: "Noodles", categories: ["Noodles"] },
  {
    id: "burgers",
    label: "Burgers",
    categories: ["Burger & Sando (served with fries)"],
  },
  { id: "poke", label: "Poke", categories: ["Poke Bowl"] },
  { id: "salads", label: "Salads", categories: ["Salads"] },
  { id: "desserts", label: "Desserts", categories: ["Desserts"] },
  {
    id: "cocktails",
    label: "Cocktails",
    categories: ["Masao Cocktails", "Classic Cocktails", "Mocktails"],
  },
  {
    id: "drinks",
    label: "Drinks",
    categories: ["Soft Drinks", "Ciders", "Beers", "Whiskey"],
  },
  {
    id: "wines",
    label: "Wines",
    categories: [
      "White Wines",
      "Rose Wines",
      "Red Wines",
      "Champagne & Sparkling",
    ],
  },
  { id: "shisha", label: "Shisha", categories: ["Shisha"] },
];

export type MenuSection = { category: string; items: MenuItem[] };
export type MenuGroup = { id: string; label: string; sections: MenuSection[] };

export const menuGroups: MenuGroup[] = GROUP_DEFS.map((group) => ({
  id: group.id,
  label: group.label,
  sections: group.categories
    .map((category) => ({
      category,
      items: menu.filter((item) => item.category === category),
    }))
    .filter((section) => section.items.length > 0),
})).filter((group) => group.sections.length > 0);
