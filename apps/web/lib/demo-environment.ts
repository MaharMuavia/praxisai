export type AppEnvironment =
  | "local"
  | "demo"
  | "test"
  | "staging"
  | "production";

export type DemoEnvironmentContract = {
  appEnvironment: AppEnvironment;
  explicitDemoMode: boolean;
  allowDemoFallback: boolean;
  showEnvironmentBanner: boolean;
};

function normalizeEnvironment(value: string | undefined): AppEnvironment {
  if (
    value === "demo" ||
    value === "test" ||
    value === "staging" ||
    value === "production"
  ) {
    return value;
  }
  return "local";
}

export function getDemoEnvironmentContract(
  environment: Record<string, string | undefined> = process.env,
): DemoEnvironmentContract {
  const appEnvironment = normalizeEnvironment(
    environment.NEXT_PUBLIC_APP_ENV ??
      environment.APP_ENV ??
      (environment.NODE_ENV === "test" ? "test" : undefined),
  );
  const explicitDemoMode =
    appEnvironment === "demo" && environment.NEXT_PUBLIC_DEMO_MODE === "true";

  return {
    appEnvironment,
    explicitDemoMode,
    allowDemoFallback:
      appEnvironment === "test" ||
      (appEnvironment === "demo" && explicitDemoMode),
    showEnvironmentBanner: explicitDemoMode,
  };
}

export function isDemoData(
  value: { is_demo?: boolean } | null | undefined,
): boolean {
  return value?.is_demo === true;
}

export const demoEnvironment = getDemoEnvironmentContract();
