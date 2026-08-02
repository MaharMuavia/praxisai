import { describe, expect, it } from "vitest";

import {
  firebasePublicEnvironmentNames,
  validatePublicBuildEnvironment,
} from "./build-env";

const hostedEnvironment = Object.fromEntries(
  firebasePublicEnvironmentNames.map((name) => [name, `${name}-value`]),
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

  it("rejects hosted builds with missing Firebase values", () => {
    expect(() =>
      validatePublicBuildEnvironment(
        { NEXT_PUBLIC_APP_ENV: "production", NEXT_PUBLIC_DEMO_MODE: "false" },
        "production",
      ),
    ).toThrow("NEXT_PUBLIC_FIREBASE_API_KEY");
  });

  it("allows explicit local and demo builds without Firebase values", () => {
    expect(() =>
      validatePublicBuildEnvironment(
        { NEXT_PUBLIC_APP_ENV: "demo", NEXT_PUBLIC_DEMO_MODE: "true" },
        "production",
      ),
    ).not.toThrow();
  });
});
