import { describe, expect, it } from "vitest";
import { getDemoEnvironmentContract, isDemoData } from "./demo-environment";

describe("demo environment contract", () => {
  it("requires explicit demo mode before showing the environment banner", () => {
    expect(
      getDemoEnvironmentContract({
        NEXT_PUBLIC_APP_ENV: "staging",
        NEXT_PUBLIC_DEMO_MODE: "false",
      }),
    ).toMatchObject({
      explicitDemoMode: false,
      showEnvironmentBanner: false,
      allowDemoFallback: false,
    });
  });

  it("shows an explicit demo environment and permits fallback", () => {
    expect(
      getDemoEnvironmentContract({
        NEXT_PUBLIC_APP_ENV: "demo",
        NEXT_PUBLIC_DEMO_MODE: "true",
      }),
    ).toMatchObject({
      explicitDemoMode: true,
      showEnvironmentBanner: true,
      allowDemoFallback: true,
    });
  });

  it("keeps test fallback behavior separate from demo labeling", () => {
    expect(
      getDemoEnvironmentContract({
        NEXT_PUBLIC_APP_ENV: "test",
        NEXT_PUBLIC_DEMO_MODE: "true",
      }),
    ).toMatchObject({
      explicitDemoMode: false,
      showEnvironmentBanner: false,
      allowDemoFallback: true,
    });
  });

  it("only labels records explicitly marked as fictional", () => {
    expect(isDemoData({ is_demo: true })).toBe(true);
    expect(isDemoData({ is_demo: false })).toBe(false);
    expect(isDemoData(undefined)).toBe(false);
  });
});
