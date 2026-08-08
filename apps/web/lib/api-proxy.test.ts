import { describe, expect, it } from "vitest";

import {
  buildApiProxyTarget,
  buildForwardHeaders,
  responseHeaders,
} from "./api-proxy";

describe("api proxy", () => {
  it("builds an encoded same-origin API target and preserves the query", () => {
    const target = buildApiProxyTarget(
      "https://api.example.run.app",
      ["projects", "project with spaces"],
      "?view=summary",
      "production",
    );

    expect(target.toString()).toBe(
      "https://api.example.run.app/api/v1/projects/project%20with%20spaces?view=summary",
    );
  });

  it("does not duplicate an API base that already includes /api/v1", () => {
    const target = buildApiProxyTarget(
      "http://localhost:8000/api/v1",
      ["health"],
      "",
      "local",
    );

    expect(target.toString()).toBe("http://localhost:8000/api/v1/health");
  });

  it("preserves supported request headers and removes spoofable routing headers", () => {
    const requestHeaders = new Headers({
      Cookie: "session=opaque",
      "Content-Type": "application/json",
      "X-CSRF-Token": "csrf",
      Connection: "keep-alive",
      Host: "malicious.example",
      Forwarded: "for=attacker",
      "X-Forwarded-For": "attacker",
      "X-Forwarded-Host": "attacker.example",
      "X-Forwarded-Proto": "http",
      Authorization: "Bearer attacker-token",
      "X-Service-Auth": "attacker-service-token",
    });

    const headers = buildForwardHeaders(requestHeaders, "correlation-123");

    expect(headers.get("cookie")).toBe("session=opaque");
    expect(headers.get("content-type")).toBe("application/json");
    expect(headers.get("x-csrf-token")).toBe("csrf");
    expect(headers.get("x-correlation-id")).toBe("correlation-123");
    expect(headers.has("connection")).toBe(false);
    expect(headers.has("host")).toBe(false);
    expect(headers.has("forwarded")).toBe(false);
    expect(headers.has("x-forwarded-for")).toBe(false);
    expect(headers.has("x-forwarded-host")).toBe(false);
    expect(headers.has("x-forwarded-proto")).toBe(false);
    expect(headers.has("authorization")).toBe(false);
    expect(headers.has("x-service-auth")).toBe(false);
  });

  it("rejects credentials, fragments, and insecure hosted targets", () => {
    expect(() =>
      buildApiProxyTarget(
        "http://api.example.run.app#fragment",
        [],
        "",
        "production",
      ),
    ).toThrow("credentials or fragments");
    expect(() =>
      buildApiProxyTarget("http://api.example.run.app", [], "", "staging"),
    ).toThrow("HTTPS");
  });

  it("filters hop-by-hop response headers and preserves each cookie", () => {
    const source = new Headers({
      "Content-Type": "application/json",
      "Content-Length": "10",
      "X-Request-Id": "req-1",
    });
    source.append("Set-Cookie", "praxis_session=one; Path=/; HttpOnly");
    source.append("Set-Cookie", "praxis_csrf=two; Path=/; SameSite=Lax");

    const headers = responseHeaders(source);

    expect(headers.get("content-type")).toBe("application/json");
    expect(headers.get("x-request-id")).toBe("req-1");
    expect(headers.has("content-length")).toBe(false);
    expect(headers.getSetCookie()).toEqual([
      "praxis_session=one; Path=/; HttpOnly",
      "praxis_csrf=two; Path=/; SameSite=Lax",
    ]);
  });
});
