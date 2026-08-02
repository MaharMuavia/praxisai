import type { QueryClient } from "@tanstack/react-query";
import { apiBase } from "../api";

export async function fetchQuery<T>(
  path: string,
  signal: AbortSignal,
): Promise<T> {
  return fetch(`${apiBase}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    signal,
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  });
}

export function retryTransientError(
  failureCount: number,
  error: Error,
): boolean {
  if (
    failureCount >= 2 ||
    /Request failed \((401|403|409|422)\)/.test(error.message)
  ) {
    return false;
  }
  return true;
}

export function invalidateScope(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
) {
  return queryClient.invalidateQueries({ queryKey });
}
