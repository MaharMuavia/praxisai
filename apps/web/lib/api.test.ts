import { describe, expect, it } from "vitest";
import { allowsDemoFallback, resolveApiBase } from "./api";

describe("frontend API environment boundary", () => {
  it("uses same-origin routing when no public API override is configured", () => {
    expect(resolveApiBase(undefined, "production", "production")).toBe(
      "/api/v1",
    );
  });

  it("rejects localhost overrides for hosted builds", () => {
    expect(() =>
      resolveApiBase("http://localhost:8000/api/v1", "staging", "production"),
    ).toThrow(/cannot point to localhost/i);
  });

  it("allows localhost only for explicit local/demo builds", () => {
    expect(
      resolveApiBase("http://localhost:8000/api/v1", "demo", "production"),
    ).toBe("http://localhost:8000/api/v1");
    expect(allowsDemoFallback("production", "demo", true)).toBe(true);
    expect(allowsDemoFallback("production", "staging", true)).toBe(false);
  });
});
