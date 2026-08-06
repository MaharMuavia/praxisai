import { describe, expect, it } from "vitest";
import { publicSecurityHeaders } from "./security-headers";

function asMap(environment: string) {
  return new Map(
    publicSecurityHeaders(environment, "production").map(({ key, value }) => [
      key,
      value,
    ]),
  );
}

describe("public security headers", () => {
  it("allows only the required Firebase, Google, and application resources", () => {
    const headers = asMap("staging");
    const csp = headers.get("Content-Security-Policy") ?? "";

    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("https://*.googleapis.com");
    expect(csp).toContain("https://securetoken.googleapis.com");
    expect(csp).toContain("https://identitytoolkit.googleapis.com");
    expect(csp).toContain("https://accounts.google.com");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(headers.get("X-Frame-Options")).toBe("DENY");
    expect(headers.has("Strict-Transport-Security")).toBe(false);
  });

  it("enables HSTS only in production", () => {
    const headers = asMap("production");

    expect(headers.get("Strict-Transport-Security")).toBe(
      "max-age=31536000; includeSubDomains",
    );
  });

  it("allows React development diagnostics without weakening production CSP", () => {
    const csp = new Map(
      publicSecurityHeaders("local", "development").map(({ key, value }) => [
        key,
        value,
      ]),
    ).get("Content-Security-Policy");

    expect(csp).toContain("'unsafe-eval'");
  });
});
