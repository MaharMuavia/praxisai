export const supabasePublicEnvironmentNames = [
  "NEXT_PUBLIC_SUPABASE_URL",
  "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
] as const;

type BuildEnvironment = Record<string, string | undefined>;

export function parseSupabaseBrowserOrigin(value: string): URL {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL must be a valid HTTPS origin");
  }
  if (
    url.protocol !== "https:" ||
    !url.hostname ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL must be a valid HTTPS origin");
  }
  return url;
}

export function validatePublicBuildEnvironment(
  environment: BuildEnvironment,
  nodeEnvironment: string,
): void {
  const appEnvironment = environment.NEXT_PUBLIC_APP_ENV;
  const hostedBuild =
    appEnvironment === "staging" ||
    appEnvironment === "production" ||
    (nodeEnvironment === "production" &&
      !["local", "demo", "test"].includes(appEnvironment ?? ""));
  if (!hostedBuild) {
    return;
  }

  const missing = supabasePublicEnvironmentNames.filter(
    (name) => !environment[name]?.trim(),
  );
  if (missing.length > 0) {
    throw new Error(
      `Hosted web builds require Supabase browser configuration: ${missing.join(", ")}`,
    );
  }
  parseSupabaseBrowserOrigin(environment.NEXT_PUBLIC_SUPABASE_URL!);
  if (environment.NEXT_PUBLIC_DEMO_MODE !== "false") {
    throw new Error("Hosted web builds require NEXT_PUBLIC_DEMO_MODE=false");
  }
}
