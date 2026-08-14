import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET, POST } from "../app/api/v1/[...path]/route";

vi.mock("google-auth-library", () => ({
  GoogleAuth: class {
    async getIdTokenClient() {
      throw new Error("service authentication unavailable in unit tests");
    }
  },
}));

describe("same-origin API route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("forwards a browser health request to the configured API", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    const fetchMock = vi.fn(
      async (input: string | URL | Request, init?: RequestInit) => {
        expect(String(input)).toBe(
          "http://localhost:8000/api/v1/health?check=1",
        );
        expect(init?.method).toBe("GET");
        expect(new Headers(init?.headers).get("cookie")).toBe("session=opaque");
        return new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "X-Correlation-Id": "corr-1",
          },
        });
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new NextRequest("http://localhost/api/v1/health?check=1", {
        headers: { Cookie: "session=opaque", "X-Correlation-Id": "corr-1" },
      }),
      { params: Promise.resolve({ path: ["health"] }) },
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("does not expose demo data when the proxy is unavailable", async () => {
    vi.stubEnv("APP_ENV", "staging");
    vi.stubEnv("API_BASE_URL", "https://api.example.run.app");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("API unavailable");
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost/api/v1/health"),
      { params: Promise.resolve({ path: ["health"] }) },
    );

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({
      detail: "API service unavailable",
    });
  });

  it("streams a request body upstream without buffering it", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    const request = new NextRequest("http://localhost/api/v1/uploads", {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: "streamed-body",
    });
    const requestBody = request.body;
    expect(requestBody).not.toBeNull();
    const arrayBufferSpy = vi.spyOn(request, "arrayBuffer");
    const fetchMock = vi.fn(
      async (input: string | URL | Request, init?: RequestInit) => {
        expect(String(input)).toBe("http://localhost:8000/api/v1/uploads");
        expect(init?.body).toBe(requestBody);
        expect(init).toHaveProperty("duplex", "half");
        expect(new Headers(init?.headers).get("content-type")).toBe(
          "application/octet-stream",
        );
        return new Response(null, { status: 204 });
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(request, {
      params: Promise.resolve({ path: ["uploads"] }),
    });

    expect(response.status).toBe(204);
    expect(arrayBufferSpy).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("uses the configured timeout and reports an upstream timeout", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    vi.stubEnv("API_PROXY_TIMEOUT_MS", "300000");
    const timeoutController = new AbortController();
    timeoutController.abort(
      new DOMException("The operation timed out", "TimeoutError"),
    );
    vi.spyOn(AbortSignal, "timeout").mockImplementation((timeoutMs) => {
      expect(timeoutMs).toBe(300_000);
      return timeoutController.signal;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_input: string | URL | Request, init?: RequestInit) => {
        expect(init?.signal?.aborted).toBe(true);
        throw init?.signal?.reason;
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost/api/v1/projects"),
      { params: Promise.resolve({ path: ["projects"] }) },
    );

    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ detail: "API service timed out" });
  });

  it("rejects invalid timeout configuration before contacting the API", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    vi.stubEnv("API_PROXY_TIMEOUT_MS", "300001");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new NextRequest("http://localhost/api/v1/health"),
      { params: Promise.resolve({ path: ["health"] }) },
    );

    expect(response.status).toBe(500);
    expect(await response.json()).toEqual({
      detail: "API proxy configuration is invalid",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("aborts the upstream request when the client disconnects", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    vi.spyOn(AbortSignal, "timeout").mockReturnValue(
      new AbortController().signal,
    );
    const clientController = new AbortController();
    let upstreamSignal: AbortSignal | undefined;
    const fetchMock = vi.fn(
      async (_input: string | URL | Request, init?: RequestInit) =>
        await new Promise<Response>((_resolve, reject) => {
          upstreamSignal = init?.signal ?? undefined;
          upstreamSignal?.addEventListener(
            "abort",
            () => reject(upstreamSignal?.reason),
            { once: true },
          );
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest("http://localhost/api/v1/uploads", {
      method: "POST",
      body: "streamed-body",
      signal: clientController.signal,
    });

    const responsePromise = POST(request, {
      params: Promise.resolve({ path: ["uploads"] }),
    });
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    clientController.abort(
      new DOMException("Client disconnected", "AbortError"),
    );
    const response = await responsePromise;

    expect(upstreamSignal?.aborted).toBe(true);
    expect(response.status).toBe(499);
  });

  it("forwards independent authentication cookies from the API", async () => {
    vi.stubEnv("APP_ENV", "local");
    vi.stubEnv("API_BASE_URL", "http://localhost:8000");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        const response = new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
        response.headers.append(
          "Set-Cookie",
          "praxis_session=session-token; Path=/; HttpOnly",
        );
        response.headers.append(
          "Set-Cookie",
          "praxis_csrf=csrf-token; Path=/; SameSite=Lax",
        );
        return response;
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost/api/v1/auth/session"),
      { params: Promise.resolve({ path: ["auth", "session"] }) },
    );

    expect(response.headers.getSetCookie()).toEqual([
      "praxis_session=session-token; Path=/; HttpOnly",
      "praxis_csrf=csrf-token; Path=/; SameSite=Lax",
    ]);
  });
});
