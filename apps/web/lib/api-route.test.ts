import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "../app/api/v1/[...path]/route";

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
});
