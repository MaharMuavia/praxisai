export const firebasePublicEnvironmentNames = [
  "NEXT_PUBLIC_FIREBASE_API_KEY",
  "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN",
  "NEXT_PUBLIC_FIREBASE_PROJECT_ID",
  "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET",
  "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID",
  "NEXT_PUBLIC_FIREBASE_APP_ID",
] as const;

type BuildEnvironment = Record<string, string | undefined>;

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

  const missing = firebasePublicEnvironmentNames.filter(
    (name) => !environment[name]?.trim(),
  );
  if (missing.length > 0) {
    throw new Error(
      `Hosted web builds require Firebase browser configuration: ${missing.join(", ")}`,
    );
  }
  if (environment.NEXT_PUBLIC_DEMO_MODE !== "false") {
    throw new Error("Hosted web builds require NEXT_PUBLIC_DEMO_MODE=false");
  }
}
