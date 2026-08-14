import { describe, expect, it } from "vitest";

import {
  supabasePublicEnvironmentNames,
  validatePublicBuildEnvironment,
} from "./build-env";

const hostedEnvironment = Object.fromEntries(
  supabasePublicEnvironmentNames.map((name) => [
    name,
    name === "NEXT_PUBLIC_SUPABASE_URL"
      ? "https://project-ref.supabase.co"
      : `${name}-value`,
  ]),
);

describe("public web build environment", () => {
  it("accepts an explicitly configured hosted build", () => {
    expect(() =>
      validatePublicBuildEnvironment(
        {
          ...hostedEnvironment,
          NEXT_PUBLIC_APP_ENV: "production",
          NEXT_PUBLIC_DEMO_MODE: "false",
        },
        "production",
      ),
    ).not.toThrow();
  });

  it("rejects hosted builds with missing Supabase values", () => {
    expect(() =>
      validatePublicBuildEnvironment(
        { NEXT_PUBLIC_APP_ENV: "production", NEXT_PUBLIC_DEMO_MODE: "false" },
        "production",
      ),
    ).toThrow("NEXT_PUBLIC_SUPABASE_URL");
  });

  it("allows explicit local and demo builds without Supabase values", () => {
    expect(() =>
      validatePublicBuildEnvironment(
        { NEXT_PUBLIC_APP_ENV: "demo", NEXT_PUBLIC_DEMO_MODE: "true" },
        "production",
      ),
    ).not.toThrow();
  });

  it.each([
    "http://project-ref.supabase.co",
    "https://user:password@project-ref.supabase.co",
    "https://project-ref.supabase.co/auth/v1",
    "https://project-ref.supabase.co?token=value",
    "not-a-url",
  ])("rejects an unsafe hosted Supabase URL: %s", (url) => {
    expect(() =>
      validatePublicBuildEnvironment(
        {
          ...hostedEnvironment,
          NEXT_PUBLIC_APP_ENV: "production",
          NEXT_PUBLIC_DEMO_MODE: "false",
          NEXT_PUBLIC_SUPABASE_URL: url,
        },
        "production",
      ),
    ).toThrow(/valid HTTPS origin/);
  });
});
