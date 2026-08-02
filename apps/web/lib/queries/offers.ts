import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Offer = components["schemas"]["OfferView"];
export const offerKeys = {
  all: ["offers"] as const,
  list: ["offers", "list"] as const,
};
export const offersQuery = () =>
  queryOptions({
    queryKey: offerKeys.list,
    queryFn: ({ signal }) => fetchQuery<Offer[]>("/assignment-offers", signal),
    retry: retryTransientError,
  });
