import { LANGUAGES, type Lang } from "@/i18n/config";
import { fetchApi } from "@/lib/fetch-api";

const ADMIN_API_BASE = "/api/admin";
const ADMIN_TIMEOUT_MS = 30_000;
// Το auto-translate περιμένει το Claude API.
const TRANSLATE_TIMEOUT_MS = 90_000;

/**
 * Every language is a translation row, Greek included: menu_items holds the
 * base text of the record without a declared language, so all nine are
 * editable and fillable targets.
 */
export const TRANSLATABLE_LANGUAGES: Lang[] = LANGUAGES.map((language) => language.code);

export function missingTranslationLanguages(translations: Record<string, unknown>): Lang[] {
  return TRANSLATABLE_LANGUAGES.filter((code) => !(code in translations));
}

export type AdminTranslationValue = { name: string; description: string };

export type AdminCategory = {
  id: number;
  name: string;
  slug: string | null;
  display_order: number;
  item_count: number;
  translations: Record<string, string>;
};

export type AdminItem = {
  id: number;
  external_id: string | null;
  category_id: number;
  category_name: string;
  name: string;
  description: string;
  price: number;
  tags: string[];
  is_available: boolean;
  display_order: number;
  translations: Record<string, AdminTranslationValue>;
};

export type ItemFilters = {
  categoryId?: number | null;
  isAvailable?: boolean | null;
  search?: string;
};

/** Το external_id δεν επεξεργάζεται από το UI: δεν υπάρχει σύνδεση με POS. */
export type ItemPayload = {
  category_id: number;
  name: string;
  description: string;
  price: number;
  tags: string[];
  is_available: boolean;
  display_order: number;
};

export type TranslateItemResult = {
  menu_item_id: number;
  translated: Lang[];
  skipped: Lang[];
  translations: Record<string, AdminTranslationValue>;
};

export type TranslateCategoryResult = {
  category_id: number;
  translated: Lang[];
  skipped: Lang[];
  translations: Record<string, string>;
};

export class AdminApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
  }
}

/** Render any thrown value as one Greek line the admin can act on. */
export function describeAdminError(cause: unknown): string {
  if (cause instanceof AdminApiError) return cause.message;
  return "Κάτι πήγε στραβά. Δοκιμάστε ξανά.";
}

export function isSessionExpired(cause: unknown): boolean {
  return cause instanceof AdminApiError && cause.status === 401;
}

/** Turn a FastAPI error body into one readable Greek-friendly line. */
function readDetail(payload: unknown, fallback: string): string {
  if (payload === null || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) =>
        entry !== null && typeof entry === "object" && typeof (entry as { msg?: unknown }).msg === "string"
          ? (entry as { msg: string }).msg
          : null,
      )
      .filter((message): message is string => message !== null);
    if (messages.length > 0) return messages.join(" · ");
  }
  return fallback;
}

async function adminFetch<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs: number = ADMIN_TIMEOUT_MS,
): Promise<T> {
  const response = await fetchApi(
    `${ADMIN_API_BASE}${path}`,
    {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init.body === undefined ? {} : { "Content-Type": "application/json" }),
        ...init.headers,
      },
      cache: "no-store",
    },
    { timeoutMs },
  );

  if (response.status === 401) {
    throw new AdminApiError(401, "Η συνεδρία έληξε. Συνδεθείτε ξανά.");
  }

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new AdminApiError(response.status, readDetail(payload, `Σφάλμα ${response.status}`));
  }
  return payload as T;
}

function itemQuery(filters: ItemFilters): string {
  const params = new URLSearchParams();
  if (filters.categoryId != null) params.set("category_id", String(filters.categoryId));
  if (filters.isAvailable != null) params.set("is_available", String(filters.isAvailable));
  if (filters.search && filters.search.trim()) params.set("search", filters.search.trim());
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function listItems(filters: ItemFilters = {}): Promise<AdminItem[]> {
  const data = await adminFetch<{ total: number; items: AdminItem[] }>(
    `/menu/items${itemQuery(filters)}`,
  );
  return data.items;
}

export async function getItem(itemId: number): Promise<AdminItem> {
  return adminFetch<AdminItem>(`/menu/items/${itemId}`);
}

export async function createItem(payload: ItemPayload): Promise<{ id: number }> {
  return adminFetch<{ id: number }>("/menu/items", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateItem(itemId: number, payload: Partial<ItemPayload>): Promise<AdminItem> {
  return adminFetch<AdminItem>(`/menu/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteItem(itemId: number): Promise<void> {
  await adminFetch<void>(`/menu/items/${itemId}`, { method: "DELETE" });
}

export async function reorderItems(itemIds: number[]): Promise<void> {
  await adminFetch<void>("/menu/items/reorder", {
    method: "PUT",
    body: JSON.stringify({ ids: itemIds }),
  });
}

export async function saveItemTranslation(
  itemId: number,
  language: Lang,
  value: AdminTranslationValue,
): Promise<void> {
  await adminFetch<void>(`/menu/items/${itemId}/translations/${language}`, {
    method: "PUT",
    body: JSON.stringify(value),
  });
}

export async function translateItem(
  itemId: number,
  options: { language_codes?: Lang[]; overwrite?: boolean } = {},
): Promise<TranslateItemResult> {
  return adminFetch<TranslateItemResult>(
    `/menu/items/${itemId}/translate`,
    { method: "POST", body: JSON.stringify(options) },
    TRANSLATE_TIMEOUT_MS,
  );
}

export async function listCategories(): Promise<AdminCategory[]> {
  const data = await adminFetch<{ total: number; categories: AdminCategory[] }>("/menu/categories");
  return data.categories;
}

export async function createCategory(payload: {
  name: string;
  slug: string | null;
  display_order: number;
}): Promise<AdminCategory> {
  return adminFetch<AdminCategory>("/menu/categories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCategory(
  categoryId: number,
  payload: { name?: string; slug?: string | null; display_order?: number },
): Promise<AdminCategory> {
  return adminFetch<AdminCategory>(`/menu/categories/${categoryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCategory(categoryId: number): Promise<void> {
  await adminFetch<void>(`/menu/categories/${categoryId}`, { method: "DELETE" });
}

export async function reorderCategories(categoryIds: number[]): Promise<void> {
  await adminFetch<void>("/menu/categories/reorder", {
    method: "PUT",
    body: JSON.stringify({ ids: categoryIds }),
  });
}

export async function saveCategoryTranslation(
  categoryId: number,
  language: Lang,
  name: string,
): Promise<void> {
  await adminFetch<void>(`/menu/categories/${categoryId}/translations/${language}`, {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
}

export async function translateCategory(
  categoryId: number,
  options: { language_codes?: Lang[]; overwrite?: boolean } = {},
): Promise<TranslateCategoryResult> {
  return adminFetch<TranslateCategoryResult>(
    `/menu/categories/${categoryId}/translate`,
    { method: "POST", body: JSON.stringify(options) },
    TRANSLATE_TIMEOUT_MS,
  );
}

export async function logout(): Promise<void> {
  await fetch("/api/admin/logout", { method: "POST" });
}
