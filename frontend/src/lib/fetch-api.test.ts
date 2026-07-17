import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchApi } from "@/lib/fetch-api";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("fetchApi", () => {
  it("aborts a request after its timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("The operation was aborted", "AbortError"));
          });
        }),
      ),
    );

    const request = fetchApi("https://example.test/menu", {}, { timeoutMs: 100 });
    const rejection = expect(request).rejects.toMatchObject({ name: "AbortError" });
    await vi.advanceTimersByTimeAsync(100);

    await rejection;
  });

  it("retries a server failure when retries are enabled", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchApi("https://example.test/menu", {}, { retries: 1 });

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does not retry a client error", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 400 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchApi("https://example.test/menu", {}, { retries: 1 });

    expect(response.status).toBe(400);
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
