import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Opportunity = components["schemas"]["OpportunityView"];
type Proposal = components["schemas"]["StudentProposalView"];
export const talentKeys = {
  all: ["talent"] as const,
  opportunities: ["talent", "opportunities"] as const,
  proposals: ["talent", "proposals"] as const,
};
export const opportunitiesQuery = () =>
  queryOptions({
    queryKey: talentKeys.opportunities,
    queryFn: ({ signal }) =>
      fetchQuery<Opportunity[]>("/talent/opportunities", signal),
    retry: retryTransientError,
  });
export const proposalsQuery = () =>
  queryOptions({
    queryKey: talentKeys.proposals,
    queryFn: ({ signal }) =>
      fetchQuery<Proposal[]>("/talent/students/me/proposals", signal),
    retry: retryTransientError,
  });
