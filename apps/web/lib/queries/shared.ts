import type { QueryClient } from "@tanstack/react-query";
import { apiBase } from "../api";

export type ApiError = Error & {
  status: number;
  code?: string;
  correlationId?: string;
  details?: Record<string, unknown>;
};

export async function parseApiError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as {
    error?: {
      code?: string;
      message?: string;
      correlation_id?: string;
      details?: Record<string, unknown>;
    };
  } | null;
  const error = new Error(
    body?.error?.message ?? `Request failed (${response.status})`,
  ) as ApiError;
  error.status = response.status;
  error.code = body?.error?.code;
  error.correlationId =
    body?.error?.correlation_id ??
    response.headers.get("X-Correlation-ID") ??
    undefined;
  error.details = body?.error?.details;
  return error;
}

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
      throw await parseApiError(response);
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
