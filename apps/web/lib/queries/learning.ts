import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type LearningPath = components["schemas"]["LearningPathView"];
export const learningKeys = {
  all: ["learning"] as const,
  paths: ["learning", "paths"] as const,
};
export const learningPathsQuery = () =>
  queryOptions({
    queryKey: learningKeys.paths,
    queryFn: ({ signal }) =>
      fetchQuery<LearningPath[]>("/learning/paths", signal),
    retry: retryTransientError,
  });
