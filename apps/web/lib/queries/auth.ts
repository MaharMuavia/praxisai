import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Session = components["schemas"]["SessionView"];
export const authKeys = {
  all: ["auth"] as const,
  session: ["auth", "session"] as const,
};
export const sessionQuery = () =>
  queryOptions({
    queryKey: authKeys.session,
    queryFn: ({ signal }) => fetchQuery<Session>("/auth/me", signal),
    retry: retryTransientError,
  });
