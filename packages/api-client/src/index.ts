import createClient from "openapi-fetch";
import type { paths } from "./schema";

export type { components, paths } from "./schema";

export function createPraxisClient(baseUrl: string) {
  return createClient<paths>({
    baseUrl,
    credentials: "include",
  });
}

export async function praxisFetch<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const csrf = typeof document === "undefined"
    ? undefined
    : document.cookie
        .split("; ")
        .find((value) => value.startsWith("praxis_csrf="))
        ?.split("=")[1];
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const message =
      typeof payload === "object" && payload !== null && "error" in payload
        ? JSON.stringify(payload)
        : `Request failed (${response.status})`;
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
