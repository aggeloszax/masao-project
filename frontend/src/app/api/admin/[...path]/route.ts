import { proxyBackendRequest } from "@/lib/server-api-proxy";

// Το auto-translate περιμένει μια κλήση στο Claude API.
export const maxDuration = 90;

type RouteContext = { params: Promise<{ path: string[] }> };

const SAFE_SEGMENT = /^[A-Za-z0-9_-]+$/;

/**
 * Forward an authenticated admin request to the FastAPI backend.
 *
 * Το INTERNAL_API_KEY μπαίνει εδώ, server-side: ο browser δεν το βλέπει ποτέ.
 * Τη συνεδρία την έχει ήδη ελέγξει το `src/proxy.ts` πριν φτάσει το request.
 */
async function forward(request: Request, context: RouteContext): Promise<Response> {
  const apiKey = process.env.INTERNAL_API_KEY?.trim();
  if (!apiKey) {
    return Response.json({ detail: "INTERNAL_API_KEY is not configured" }, { status: 503 });
  }

  const { path } = await context.params;
  if (path.length === 0 || !path.every((segment) => SAFE_SEGMENT.test(segment))) {
    return Response.json({ detail: "Invalid admin path" }, { status: 400 });
  }

  const headers: Record<string, string> = { "X-API-Key": apiKey, Accept: "application/json" };
  const hasBody = request.method !== "GET" && request.method !== "DELETE";
  let body: string | undefined;
  if (hasBody) {
    body = await request.text();
    headers["Content-Type"] = "application/json";
  }

  const { search } = new URL(request.url);
  return proxyBackendRequest(`/api/admin/${path.join("/")}${search}`, {
    method: request.method,
    headers,
    body,
  });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
