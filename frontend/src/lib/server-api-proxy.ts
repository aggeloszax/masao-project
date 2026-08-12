import "server-only";

const LOCAL_API_BASE_URL = "http://localhost:8000";

function backendBaseUrl(): string | null {
  const configured =
    process.env.API_BASE_URL?.trim() || process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  if (configured) return configured.replace(/\/+$/, "");
  return process.env.NODE_ENV === "development" ? LOCAL_API_BASE_URL : null;
}

export async function proxyBackendRequest(
  path: string,
  init: RequestInit,
): Promise<Response> {
  const baseUrl = backendBaseUrl();
  if (!baseUrl) {
    return Response.json(
      { detail: "Backend API URL is not configured" },
      { status: 503 },
    );
  }

  try {
    const upstream = await fetch(`${baseUrl}${path}`, {
      ...init,
      cache: "no-store",
    });
    const headers = new Headers();
    for (const name of ["content-type", "retry-after", "x-request-id"]) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      headers,
    });
  } catch {
    return Response.json(
      { detail: "Backend API is unavailable" },
      { status: 503 },
    );
  }
}
