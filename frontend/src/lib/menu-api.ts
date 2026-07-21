import type { MenuGroup, MenuItem } from "@/data/menu";
import type { Lang } from "@/i18n/config";
import { fetchApi } from "@/lib/fetch-api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const MENU_ENDPOINT = "/api/menu";
const MENU_TIMEOUT_MS = 30_000;

type ApiMenuResponse = {
  restaurant_slug: string;
  language_code: Lang;
  total_categories: number;
  total_items: number;
  categories: ApiMenuCategory[];
};

type ApiMenuCategory = {
  id?: number | string;
  slug?: string;
  name?: string;
  label?: string;
  category?: string;
  display_order?: number;
  items?: ApiMenuItem[];
};

type ApiMenuItem = {
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
  return data.categories.map(mapCategory).filter((group) => group.sections.length > 0);
}

function apiBaseUrl(): string {
  if (API_BASE_URL) return API_BASE_URL;
  if (typeof window !== "undefined") return window.location.origin;
  return "http://localhost:8000";
}

function mapCategory(category: ApiMenuCategory, index: number): MenuGroup {
  const label = category.name ?? category.label ?? category.category ?? `Category ${index + 1}`;
  const id = String(category.slug ?? category.id ?? slugify(label));
  const items = (category.items ?? []).map((item) => mapItem(item, label));

  return {
    id,
    label,
    sections: [
      {
        category: label,
        items,
      },
    ],
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
