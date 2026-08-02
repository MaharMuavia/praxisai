import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Credential = components["schemas"]["StudentCredentialView"];
export const credentialKeys = {
  all: ["credentials"] as const,
  mine: ["credentials", "mine"] as const,
};
export const credentialsQuery = () =>
  queryOptions({
    queryKey: credentialKeys.mine,
    queryFn: ({ signal }) =>
      fetchQuery<Credential[]>("/students/me/credentials", signal),
    retry: retryTransientError,
  });
