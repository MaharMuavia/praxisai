import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Dashboard = components["schemas"]["DashboardSummary"];
type Job = components["schemas"]["OperationsJobView"];
type Integration = components["schemas"]["IntegrationStatus"];
export const operationsKeys = {
  all: ["operations"] as const,
  dashboard: ["operations", "dashboard"] as const,
  jobs: ["operations", "jobs"] as const,
  integrations: ["operations", "integrations"] as const,
};
export const operationsDashboardQuery = () =>
  queryOptions({
    queryKey: operationsKeys.dashboard,
    queryFn: ({ signal }) => fetchQuery<Dashboard>("/ops/dashboard", signal),
    retry: retryTransientError,
  });
export const operationsJobsQuery = () =>
  queryOptions({
    queryKey: operationsKeys.jobs,
    queryFn: ({ signal }) =>
      fetchQuery<Job[]>("/ops/jobs?status=DEAD_LETTER", signal),
    retry: retryTransientError,
  });
export const integrationsQuery = () =>
  queryOptions({
    queryKey: operationsKeys.integrations,
    queryFn: ({ signal }) =>
      fetchQuery<Integration[]>("/ops/integrations", signal),
    retry: retryTransientError,
  });
