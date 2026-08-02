export function rejectsLocalhostInProduction(value: string): boolean {
  return /(^|:\/\/)(localhost|127\.0\.0\.1)(:\d+)?(?:\/|$)/i.test(value);
}

export function resolveApiBase(
  configuredValue: string | undefined,
  appEnvironment: string | undefined,
  nodeEnvironment: string,
): string {
  const configuredApiBase = configuredValue?.trim();
  const localBuildEnvironment =
    appEnvironment === "local" || appEnvironment === "demo";
  if (
    nodeEnvironment === "production" &&
    !localBuildEnvironment &&
    configuredApiBase &&
    rejectsLocalhostInProduction(configuredApiBase)
  ) {
    throw new Error(
      "NEXT_PUBLIC_API_URL cannot point to localhost in a production web build",
    );
  }
  return configuredApiBase || "/api/v1";
}

export function allowsDemoFallback(
  nodeEnvironment: string,
  appEnvironment: string | undefined,
  demoMode: boolean,
): boolean {
  return nodeEnvironment === "test" || (appEnvironment === "demo" && demoMode);
}

export const apiBase = resolveApiBase(
  process.env.NEXT_PUBLIC_API_URL,
  process.env.NEXT_PUBLIC_APP_ENV,
  process.env.NODE_ENV,
);

export const demoFallbackEnabled = allowsDemoFallback(
  process.env.NODE_ENV,
  process.env.NEXT_PUBLIC_APP_ENV,
  process.env.NEXT_PUBLIC_DEMO_MODE === "true",
);
