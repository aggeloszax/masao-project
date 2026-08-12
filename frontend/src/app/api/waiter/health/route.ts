import { proxyBackendRequest } from "@/lib/server-api-proxy";

export async function GET(): Promise<Response> {
  return proxyBackendRequest("/health", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}
