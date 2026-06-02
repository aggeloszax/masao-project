import type { Lang } from "@/i18n/config";

const DEVICE_STORAGE_KEY = "masao-device-id";
const DEFAULT_API_BASE_URL = "http://localhost:8000";
const DEFAULT_TABLE_NUMBER = 1;

export type ChatApiRole = "user" | "assistant" | "system";

export type ChatApiMessage = {
  id: number;
  session_id: string;
  role: ChatApiRole;
  content: string;
  created_at: string;
};

export type ChatApiMenuItem = {
  id: number;
  external_id: string | null;
  category: string;
  name: string;
  description: string;
  price: number;
  tags: string[];
  is_available: boolean;
  language_code: Lang;
};

export type ChatApiResponse = {
  session_id: string;
  restaurant_slug: string;
  table_number: number;
  device_id: string;
  language_code: Lang;
  assistant_message: ChatApiMessage;
  messages: ChatApiMessage[];
  recommended_items: ChatApiMenuItem[];
};

export type SendChatMessageInput = {
  restaurantSlug: string;
  tableNumber: number;
  deviceId: string;
  userMessage: string;
  languageCode: Lang;
};

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

export function getOrCreateDeviceId(): string {
  const existing = window.localStorage.getItem(DEVICE_STORAGE_KEY);
  if (existing) return existing;

  const next =
    typeof window.crypto?.randomUUID === "function"
      ? window.crypto.randomUUID()
      : `device-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  window.localStorage.setItem(DEVICE_STORAGE_KEY, next);
  return next;
}

export function getTableNumberFromUrl(): number {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("table") ?? params.get("table_number") ?? params.get("t");
  const parsed = Number.parseInt(raw ?? "", 10);

  if (Number.isInteger(parsed) && parsed > 0 && parsed <= 999) {
    return parsed;
  }
  return DEFAULT_TABLE_NUMBER;
}

export async function sendChatMessage(input: SendChatMessageInput): Promise<ChatApiResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      restaurant_slug: input.restaurantSlug,
      table_number: input.tableNumber,
      device_id: input.deviceId,
      user_message: input.userMessage,
      language_code: input.languageCode,
    }),
  });

  if (!response.ok) {
    let detail = `Chat request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep the status-based message when the server does not return JSON.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<ChatApiResponse>;
}
