import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "../app/api/v1/[...path]/route";

vi.mock("google-auth-library", () => ({
  GoogleAuth: class {
    async getIdTokenClient() {
      throw new Error("service authentication unavailable in unit tests");
    }
  },
}));

describe("same-origin API route", () => {
  afterEach(() => {
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
