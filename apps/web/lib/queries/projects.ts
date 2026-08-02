import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Project = components["schemas"]["ProjectView"];
type ProjectWorkspace = components["schemas"]["ProjectWorkspaceView"];
export const projectKeys = {
  all: ["projects"] as const,
  list: ["projects", "list"] as const,
  workspace: (id: string) => ["projects", "workspace", id] as const,
};
export const projectsQuery = () =>
  queryOptions({
    queryKey: projectKeys.list,
    queryFn: ({ signal }) =>
      fetchQuery<{ items: Project[] }>("/projects", signal),
    retry: retryTransientError,
  });
export const projectWorkspaceQuery = (id: string) =>
  queryOptions({
    queryKey: projectKeys.workspace(id),
    queryFn: ({ signal }) =>
      fetchQuery<ProjectWorkspace>(`/projects/${id}/workspace`, signal),
    retry: retryTransientError,
    enabled: Boolean(id),
  });
