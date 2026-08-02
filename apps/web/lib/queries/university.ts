import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Metrics = components["schemas"]["UniversityMetrics"];
type ExportJob = components["schemas"]["UniversityExportView"];
export const universityKeys = {
  all: ["university"] as const,
  metrics: ["university", "metrics"] as const,
  exports: ["university", "exports"] as const,
};
export const universityMetricsQuery = () =>
  queryOptions({
    queryKey: universityKeys.metrics,
    queryFn: ({ signal }) => fetchQuery<Metrics>("/university/metrics", signal),
    retry: retryTransientError,
  });
export const universityExportsQuery = () =>
  queryOptions({
    queryKey: universityKeys.exports,
    queryFn: ({ signal }) =>
      fetchQuery<ExportJob[]>("/university/exports", signal),
    retry: retryTransientError,
  });
