import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Invoice = components["schemas"]["ClientInvoiceView"];
type EarningsItem = components["schemas"]["EarningsItemView"];
export const billingKeys = {
  all: ["billing"] as const,
  invoices: ["billing", "invoices"] as const,
  earnings: ["billing", "earnings"] as const,
};
export const invoicesQuery = () =>
  queryOptions({
    queryKey: billingKeys.invoices,
    queryFn: ({ signal }) => fetchQuery<Invoice[]>("/client/invoices", signal),
    retry: retryTransientError,
  });
export const earningsQuery = () =>
  queryOptions({
    queryKey: billingKeys.earnings,
    queryFn: ({ signal }) =>
      fetchQuery<EarningsItem[]>("/participants/me/earnings", signal),
    retry: retryTransientError,
  });
