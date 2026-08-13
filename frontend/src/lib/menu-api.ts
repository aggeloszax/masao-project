import {
  MENU_GROUP_DEFS,
  type MenuGroup,
  type MenuGroupDefinition,
  type MenuItem,
  type MenuSection,
} from "@/data/menu";
import type { Lang } from "@/i18n/config";
import { fetchApi } from "@/lib/fetch-api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const MENU_ENDPOINT = "/api/menu";
const MENU_TIMEOUT_MS = 30_000;

export type ApiMenuResponse = {
  restaurant_slug: string;
  language_code: Lang;
  total_categories: number;
  total_items: number;
  categories: ApiMenuCategory[];
};

export type ApiMenuCategory = {
  id?: number | string;
  slug?: string;
  name?: string;
  label?: string;
  category?: string;
  display_order?: number;
  items?: ApiMenuItem[];
};

export type ApiMenuItem = {
  id?: number | string;
  external_id?: string;
  name: string;
  description?: string | null;
  category?: string | null;
  category_name?: string | null;
  price: number | string;
  tags?: string[] | null;
};

export async function fetchMenuGroups(lang: Lang): Promise<MenuGroup[]> {
  const url = new URL(MENU_ENDPOINT, apiBaseUrl());
  url.searchParams.set("language_code", lang);

  const response = await fetchApi(
    url,
    {
      headers: { Accept: "application/json" },
      cache: "no-store",
    },
    { timeoutMs: MENU_TIMEOUT_MS, retries: 1 },
  );

  if (!response.ok) {
    throw new Error(`Menu request failed with ${response.status}`);
  }

  const data = (await response.json()) as ApiMenuResponse;
  return mapMenuCategories(data.categories);
}

function apiBaseUrl(): string {
  if (API_BASE_URL) return API_BASE_URL;
  if (typeof window !== "undefined") return window.location.origin;
  return "http://localhost:8000";
}

const GROUP_BY_CATEGORY_SLUG = new Map<string, MenuGroupDefinition>(
  MENU_GROUP_DEFS.flatMap((group) =>
    group.categories.map((category) => [slugify(category), group] as const),
  ),
);

/**
 * Convert raw API categories to the same stable high-level groups used by the
 * bundled menu. Category slugs are canonical; translated labels are display
 * data and must never become navigation identifiers.
 */
export function mapMenuCategories(categories: ApiMenuCategory[]): MenuGroup[] {
  const knownGroups = new Map<string, MenuGroup>();
  const unknownGroups: MenuGroup[] = [];

  const orderedCategories = [...categories].sort(
    (left, right) =>
      (left.display_order ?? Number.MAX_SAFE_INTEGER) -
      (right.display_order ?? Number.MAX_SAFE_INTEGER),
  );

  for (const [index, category] of orderedCategories.entries()) {
    const mapped = mapCategory(category, index);
    if (mapped.section.items.length === 0) continue;

    const definition = GROUP_BY_CATEGORY_SLUG.get(mapped.slug);
    if (!definition) {
      unknownGroups.push({
        id: mapped.slug,
        label: mapped.label,
        sections: [mapped.section],
      });
      continue;
    }

    const existing = knownGroups.get(definition.id);
    if (existing) {
      existing.sections.push(mapped.section);
      continue;
    }

    knownGroups.set(definition.id, {
      id: definition.id,
      label: definition.label,
      sections: [mapped.section],
    });
  }

  const groupedMenu = MENU_GROUP_DEFS.flatMap((definition) => {
    const group = knownGroups.get(definition.id);
    return group ? [group] : [];
  });

  return [...groupedMenu, ...unknownGroups];
}

function mapCategory(
  category: ApiMenuCategory,
  index: number,
): { slug: string; label: string; section: MenuSection } {
  const label = category.name ?? category.label ?? category.category ?? `Category ${index + 1}`;
  const slug = String(category.slug ?? category.id ?? slugify(label));
  const items = (category.items ?? []).map((item) => mapItem(item, label));

  return {
    slug,
    label,
    section: {
      category: label,
      items,
    },
  };
}

function mapItem(item: ApiMenuItem, category: string): MenuItem {
  const id = String(item.external_id ?? item.id ?? item.name);
  const description = item.description ?? "";
  const normalizedCategory = item.category ?? item.category_name ?? category;

  return {
    id,
    name: item.name,
    price: typeof item.price === "number" ? item.price : Number(item.price),
    description,
    category: normalizedCategory,
    tags: item.tags ?? [],
    translations: {},
  };
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
}
