import { describe, expect, it } from "vitest";
import {
  safeAuthCallbackDestination,
  studentSignupEmailRedirect,
} from "./auth-redirect";

const PROGRAM_ID = "11111111-1111-4111-8111-111111111111";
const COHORT_ID = "22222222-2222-4222-8222-222222222222";

describe("Supabase auth redirects", () => {
  it("preserves only valid signup context in the confirmation callback", () => {
    const redirect = new URL(
      studentSignupEmailRedirect(
        "https://app.praxis.example",
        PROGRAM_ID,
        COHORT_ID,
      ),
    );

    expect(redirect.origin).toBe("https://app.praxis.example");
    expect(redirect.pathname).toBe("/auth/callback");
    expect(redirect.searchParams.get("next")).toBe(
      `/auth/student-signup?program=${PROGRAM_ID}&cohort=${COHORT_ID}`,
    );
  });

  it("rejects external and malformed callback destinations", () => {
    expect(
      safeAuthCallbackDestination("https://attacker.example/collect"),
    ).toBe("/auth/student-signup");
    expect(safeAuthCallbackDestination("javascript:alert(1)")).toBe(
      "/auth/student-signup",
    );
    expect(
      safeAuthCallbackDestination(
        `/auth/student-signup?program=${PROGRAM_ID}&cohort=not-a-uuid&extra=ignored`,
      ),
    ).toBe(`/auth/student-signup?program=${PROGRAM_ID}`);
  });
});
