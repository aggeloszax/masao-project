import type { Lang } from "@/i18n/config";
import { fetchApi } from "@/lib/fetch-api";
import { parseTableNumber } from "@/lib/table-context";

const DEVICE_STORAGE_KEY = "masao-device-id";
const DEFAULT_API_BASE_URL = "http://localhost:8000";
const CHAT_TIMEOUT_MS = 75_000;
const WARMUP_TIMEOUT_MS = 30_000;

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

export class ChatApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "ChatApiError";
  }
}

export type SendChatMessageInput = {
  restaurantSlug: string;
  tableNumber: number;
  deviceId: string;
  conversationId: string;
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

export function getTableNumberFromUrl(): number | null {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("table") ?? params.get("table_number") ?? params.get("t");
  return parseTableNumber(raw);
}

export async function warmChatApi(): Promise<void> {
  try {
    await fetchApi(
      `${getApiBaseUrl()}/health`,
      { headers: { Accept: "application/json" } },
      { timeoutMs: WARMUP_TIMEOUT_MS },
    );
  } catch {
    // Best effort only: the request still wakes a sleeping Render instance.
  }
}

export async function sendChatMessage(input: SendChatMessageInput): Promise<ChatApiResponse> {
  const response = await fetchApi(`${getApiBaseUrl()}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      restaurant_slug: input.restaurantSlug,
      table_number: input.tableNumber,
      device_id: input.deviceId,
      conversation_id: input.conversationId,
      user_message: input.userMessage,
      language_code: input.languageCode,
    }),
  }, { timeoutMs: CHAT_TIMEOUT_MS });

  if (!response.ok) {
    let detail = `Chat request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep the status-based message when the server does not return JSON.
    }
    throw new ChatApiError(
      detail,
      response.status,
      parseRetryAfter(response.headers.get("Retry-After")),
    );
  }

  return response.json() as Promise<ChatApiResponse>;
}

function parseRetryAfter(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = Number(value);
  return Number.isFinite(seconds) ? seconds : undefined;
}
