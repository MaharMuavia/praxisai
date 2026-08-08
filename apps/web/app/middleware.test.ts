import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { proxy } from "../proxy";

function request(url: string, headers?: HeadersInit): NextRequest {
  return new NextRequest(`https://praxis.example${url}`, { headers });
}

describe("proxy", () => {
  it("redirects unauthenticated workspace requests and preserves the destination", () => {
    const response = proxy(request("/student/projects?view=active"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "https://praxis.example/login?redirect=%2Fstudent%2Fprojects%3Fview%3Dactive",
    );
    expect(response.headers.get("x-correlation-id")).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
  });

  it("allows a session into the workspace and forwards the correlation ID", () => {
    const response = proxy(
      request("/ops", {
        Cookie: "praxis_session=session-token",
        "X-Correlation-ID": "corr-123",
      }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("x-correlation-id")).toBe("corr-123");
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });

  it("allows public routes without a session", () => {
    const response = proxy(request("/internships/example/apply"));

    expect(response.status).toBe(200);
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });
});
