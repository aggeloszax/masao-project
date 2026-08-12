import { proxyBackendRequest } from "@/lib/server-api-proxy";

export const maxDuration = 90;

export async function POST(request: Request): Promise<Response> {
  return proxyBackendRequest("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await request.text(),
  });
}
