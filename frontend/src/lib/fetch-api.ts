export const DEFAULT_API_TIMEOUT_MS = 15_000;

type FetchApiOptions = {
  timeoutMs?: number;
  retries?: number;
};

export async function fetchApi(
  input: RequestInfo | URL,
  init: RequestInit = {},
  options: FetchApiOptions = {},
): Promise<Response> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_API_TIMEOUT_MS;
  const retries = Math.max(0, options.retries ?? 0);

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(input, { ...init, signal: controller.signal });
      if (response.status >= 500 && attempt < retries) continue;
      return response;
    } catch (error) {
      if (attempt >= retries) throw error;
    } finally {
      globalThis.clearTimeout(timeoutId);
    }
  }

  throw new Error("API request failed");
}
