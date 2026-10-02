import type { Lang } from "@/i18n/config";
import { fetchApi } from "@/lib/fetch-api";

const TAKEAWAY_ENDPOINT = "/api/orders/takeaway";
const ORDER_TIMEOUT_MS = 30_000;

export type TakeawayOrderInput = {
  customerName: string;
  customerPhone: string;
  language: Lang;
  items: { itemRef: string; quantity: number; note: string }[];
};

export type TakeawayOrderResult = { orderId: string; total: number };

export class OrderError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "OrderError";
    this.status = status;
  }
}

/**
 * Submit a take-away order.
 *
 * Οι τιμές δεν στέλνονται: το backend τις διαβάζει από το μενού και
 * υπολογίζει το σύνολο μόνο του.
 */
export async function submitTakeawayOrder(
  input: TakeawayOrderInput,
): Promise<TakeawayOrderResult> {
  const response = await fetchApi(
    TAKEAWAY_ENDPOINT,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      cache: "no-store",
      body: JSON.stringify({
        customer_name: input.customerName,
        customer_phone: input.customerPhone,
        language_code: input.language,
        items: input.items.map((item) => ({
          item_ref: item.itemRef,
          quantity: item.quantity,
          note: item.note,
        })),
      }),
    },
    { timeoutMs: ORDER_TIMEOUT_MS },
  );

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail =
      payload !== null && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : `Order failed with ${response.status}`;
    throw new OrderError(response.status, detail);
  }

  const data = payload as { order_id: string; total: number };
  return { orderId: data.order_id, total: data.total };
}
