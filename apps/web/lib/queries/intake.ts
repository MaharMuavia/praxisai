import { queryOptions } from "@tanstack/react-query";
import { fetchQuery, retryTransientError } from "./shared";

export type IntakeStatus =
  | "NEW"
  | "IN_REVIEW"
  | "QUALIFIED"
  | "REJECTED"
  | "CONVERTED";
export type IntakeSubmission = {
  id: string;
  kind: "company" | "student" | "expert_lead" | "university";
  status: IntakeStatus;
  contact_email: string;
  source: string | null;
  campaign: string | null;
  payload: Record<string, unknown>;
  owner_id: string | null;
  qualification_notes: string | null;
  rejection_reason: string | null;
  reviewed_at: string | null;
  created_at: string;
  correlation_id: string;
  version: number;
  conversion_evidence: string | null;
  retention_expires_at: string | null;
  anonymized_at: string | null;
};

export const intakeKeys = {
  all: ["intake"] as const,
  list: (status: string) => ["intake", "list", status] as const,
  detail: (id: string) => ["intake", "detail", id] as const,
};

export const intakeQueueQuery = (status: string) =>
  queryOptions({
    queryKey: intakeKeys.list(status),
    queryFn: ({ signal }) =>
      fetchQuery<IntakeSubmission[]>(
        `/ops/intake${status ? `?status=${encodeURIComponent(status)}` : ""}`,
        signal,
      ),
    retry: retryTransientError,
  });

export const intakeDetailQuery = (id: string) =>
  queryOptions({
    queryKey: intakeKeys.detail(id),
    queryFn: ({ signal }) =>
      fetchQuery<IntakeSubmission>(`/ops/intake/${id}`, signal),
    retry: retryTransientError,
  });
