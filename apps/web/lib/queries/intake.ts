import { queryOptions } from "@tanstack/react-query";
import { fetchQuery, retryTransientError } from "./shared";

export type IntakeStatus =
  | "NEW"
  | "IN_REVIEW"
  | "QUALIFIED"
  | "REJECTED"
  | "CONVERTED";
export type IntakeKind = "company" | "student" | "expert_lead" | "university";
export type IntakeSubmission = {
  id: string;
  kind: IntakeKind;
  status: IntakeStatus;
  contact_email: string | null;
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
  deleted_at: string | null;
  withdrawal_requested_at: string | null;
  allowed_transitions: IntakeStatus[];
};
export type IntakeSummary = Pick<
  IntakeSubmission,
  | "id"
  | "kind"
  | "status"
  | "source"
  | "campaign"
  | "owner_id"
  | "created_at"
  | "retention_expires_at"
  | "anonymized_at"
  | "withdrawal_requested_at"
> & { display_name: string; action_required: boolean };
export type IntakeQueueResponse = {
  items: IntakeSummary[];
  next_cursor: string | null;
};
export type IntakeOwner = { id: string; display_name: string; email: string };
export type IntakeAudit = {
  id: string;
  action: string;
  resource_id: string | null;
  correlation_id: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export const intakeKeys = {
  all: ["intake"] as const,
  list: (params: string) => ["intake", "list", params] as const,
  detail: (id: string) => ["intake", "detail", id] as const,
  owners: ["intake", "owners"] as const,
  audit: (id: string) => ["intake", "audit", id] as const,
};

export function intakeQueueQuery(params: URLSearchParams) {
  const query = params.toString();
  return queryOptions({
    queryKey: intakeKeys.list(query),
    queryFn: ({ signal }) =>
      fetchQuery<IntakeQueueResponse>(
        `/ops/intake${query ? `?${query}` : ""}`,
        signal,
      ),
    retry: retryTransientError,
  });
}

export const intakeDetailQuery = (id: string) =>
  queryOptions({
    queryKey: intakeKeys.detail(id),
    queryFn: ({ signal }) =>
      fetchQuery<IntakeSubmission>(`/ops/intake/${id}`, signal),
    retry: retryTransientError,
  });

export const intakeOwnersQuery = () =>
  queryOptions({
    queryKey: intakeKeys.owners,
    queryFn: ({ signal }) =>
      fetchQuery<IntakeOwner[]>("/ops/intake/owners", signal),
    retry: retryTransientError,
  });

export const intakeAuditQuery = (id: string) =>
  queryOptions({
    queryKey: intakeKeys.audit(id),
    queryFn: ({ signal }) =>
      fetchQuery<IntakeAudit[]>(`/ops/intake/${id}/audit`, signal),
    retry: retryTransientError,
  });
