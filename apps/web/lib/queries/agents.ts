import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type AgentRun = components["schemas"]["AgentRunView"];
export const agentKeys = {
  all: ["agents"] as const,
  runs: ["agents", "runs"] as const,
};
export const agentRunsQuery = () =>
  queryOptions({
    queryKey: agentKeys.runs,
    queryFn: ({ signal }) => fetchQuery<AgentRun[]>("/ops/agent-runs", signal),
    retry: retryTransientError,
  });
