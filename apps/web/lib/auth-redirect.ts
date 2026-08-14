const STUDENT_SIGNUP_PATH = "/auth/student-signup";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function validId(value: string | null): string | null {
  const normalized = value?.trim() ?? "";
  return UUID_PATTERN.test(normalized) ? normalized : null;
}

export function studentSignupPath(
  programId: string | null,
  cohortId: string | null,
): string {
  const params = new URLSearchParams();
  const program = validId(programId);
  const cohort = validId(cohortId);
  if (program) params.set("program", program);
  if (cohort) params.set("cohort", cohort);
  const query = params.toString();
  return query ? `${STUDENT_SIGNUP_PATH}?${query}` : STUDENT_SIGNUP_PATH;
}

export function studentSignupEmailRedirect(
  origin: string,
  programId: string | null,
  cohortId: string | null,
): string {
  const callback = new URL("/auth/callback", origin);
  if (!new Set(["http:", "https:"]).has(callback.protocol)) {
    throw new Error("The application origin must use HTTP or HTTPS");
  }
  callback.searchParams.set("next", studentSignupPath(programId, cohortId));
  return callback.toString();
}

export function safeAuthCallbackDestination(candidate: string | null): string {
  if (!candidate || candidate.length > 2_000) return STUDENT_SIGNUP_PATH;
  try {
    const base = new URL("https://praxis.invalid");
    const parsed = new URL(candidate, base);
    if (
      parsed.origin !== base.origin ||
      parsed.pathname !== STUDENT_SIGNUP_PATH
    ) {
      return STUDENT_SIGNUP_PATH;
    }
    return studentSignupPath(
      parsed.searchParams.get("program"),
      parsed.searchParams.get("cohort"),
    );
  } catch {
    return STUDENT_SIGNUP_PATH;
  }
}
