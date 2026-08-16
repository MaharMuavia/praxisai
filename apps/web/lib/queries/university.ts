import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { apiBase } from "../api";
import { fetchQuery, parseApiError, retryTransientError } from "./shared";

export type UniversityMetrics = components["schemas"]["UniversityMetrics"];
export type UniversityExportJob = components["schemas"]["UniversityExportView"];
export type UniversityExportRequest =
  components["schemas"]["UniversityExportRequest"];
export type SkillPathwayMetric = components["schemas"]["SkillPathwayMetric"];
export type AccreditationStandardSummary =
  components["schemas"]["AccreditationStandardSummary"];

export const universityKeys = {
  all: ["university"] as const,
  metrics: ["university", "metrics"] as const,
  exports: ["university", "exports"] as const,
};

export const universityMetricsQuery = () =>
  queryOptions({
    queryKey: universityKeys.metrics,
    queryFn: ({ signal }) =>
      fetchQuery<UniversityMetrics>("/university/metrics", signal),
    retry: retryTransientError,
  });

export const universityExportsQuery = () =>
  queryOptions({
    queryKey: universityKeys.exports,
    queryFn: ({ signal }) =>
      fetchQuery<UniversityExportJob[]>("/university/exports", signal),
    retry: retryTransientError,
  });

export async function requestUniversityExport(
  payload: UniversityExportRequest,
): Promise<UniversityExportJob> {
  const response = await fetch(`${apiBase}/university/exports`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
      "X-CSRF-Token": document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response);
  }
  return response.json();
}
