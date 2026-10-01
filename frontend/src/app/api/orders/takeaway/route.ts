import { proxyBackendRequest } from "@/lib/server-api-proxy";

export const maxDuration = 30;

export async function POST(request: Request): Promise<Response> {
  return proxyBackendRequest("/api/orders/takeaway", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await request.text(),
  });
}
