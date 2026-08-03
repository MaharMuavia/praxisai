"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { apiBase } from "../../lib/api";
import {
  fetchQuery,
  parseApiError,
  retryTransientError,
} from "../../lib/queries/shared";
import {
  integrationsQuery,
  operationsJobsQuery,
  operationsKeys,
} from "../../lib/queries/operations";
import { offersQuery, offerKeys } from "../../lib/queries/offers";
import {
  universityExportsQuery,
  universityMetricsQuery,
  universityKeys,
} from "../../lib/queries/university";
import { RoleWorkspaceRecords } from "../../components/role-workspace-records";

type Mode = "jobs" | "offers" | "exports" | "approvals" | "risks";
type ExportJob = components["schemas"]["UniversityExportView"];

function useQueue<T>(key: readonly unknown[], path: string, enabled: boolean) {
  return useQuery({
    queryKey: key,
    enabled,
    queryFn: ({ signal }) => fetchQuery<T>(path, signal),
    retry: retryTransientError,
  });
}

export function IsolatedWorkspacePage({ mode }: { mode: Mode }) {
  const client = useQueryClient();
  const [reason, setReason] = useState("");
  const [purpose, setPurpose] = useState("");
  const jobs = useQuery({ ...operationsJobsQuery(), enabled: mode === "jobs" });
  const integrations = useQuery({
    ...integrationsQuery(),
    enabled: mode === "jobs",
  });
  const offers = useQuery({ ...offersQuery(), enabled: mode === "offers" });
  const exportsQuery = useQuery({
    ...universityExportsQuery(),
    enabled: mode === "exports",
  });
  const metrics = useQuery({
    ...universityMetricsQuery(),
    enabled: mode === "exports",
  });
  const approvals = useQueue<components["schemas"]["ApprovalQueueItem"][]>(
    operationsKeys.approvals,
    "/ops/approval-queue",
    mode === "approvals",
  );
  const risks = useQueue<components["schemas"]["RiskQueueItem"][]>(
    operationsKeys.risks,
    "/ops/risk-queue",
    mode === "risks",
  );
  const recover = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await fetch(`${apiBase}/ops/jobs/${jobId}/recover`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
          "X-CSRF-Token":
            document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
        },
        body: JSON.stringify({ reason }),
      });
      if (!response.ok) throw await parseApiError(response);
      return response.json();
    },
    onSuccess: () => {
      setReason("");
      void client.invalidateQueries({ queryKey: operationsKeys.jobs });
    },
  });
  const decideOffer = useMutation({
    mutationFn: async ({
      id,
      decision,
    }: {
      id: string;
      decision: "accept" | "decline";
    }) => {
      const response = await fetch(
        `${apiBase}/assignment-offers/${id}/${decision}`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": crypto.randomUUID(),
            "X-CSRF-Token":
              document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
          },
          body: JSON.stringify({ expected_state: "OFFERED" }),
        },
      );
      if (!response.ok) throw await parseApiError(response);
      return response.json();
    },
    onSuccess: () =>
      void client.invalidateQueries({ queryKey: offerKeys.list }),
  });
  const requestExport = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${apiBase}/university/exports`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
          "X-CSRF-Token":
            document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
        },
        body: JSON.stringify({ purpose }),
      });
      if (!response.ok) throw await parseApiError(response);
      return response.json();
    },
    onSuccess: () => {
      setPurpose("");
      void client.invalidateQueries({ queryKey: universityKeys.exports });
    },
  });
  if (mode === "offers")
    return (
      <RoleWorkspaceRecords
        data={{ kind: "offers", items: offers.data ?? null }}
        onOfferDecision={(id, decision) => decideOffer.mutate({ id, decision })}
        submittingOfferId={decideOffer.isPending ? "busy" : null}
      />
    );
  if (mode === "approvals")
    return (
      <RoleWorkspaceRecords
        data={{ kind: "approvals", items: approvals.data ?? null }}
      />
    );
  if (mode === "risks")
    return (
      <RoleWorkspaceRecords
        data={{ kind: "risks", items: risks.data ?? null }}
      />
    );
  if (mode === "jobs")
    return (
      <div className="data-list">
        <h2>Dead-letter jobs</h2>
        <label>
          Recovery reason
          <textarea
            minLength={20}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            rows={3}
          />
        </label>
        {(integrations.data ?? []).map((item) => (
          <div className="data-row" key={item.provider}>
            <span>
              <strong>{item.provider}</strong>
              <small>{item.mode}</small>
            </span>
            <span className="status-badge">
              {item.configured ? "Configured" : "Needs setup"}
            </span>
          </div>
        ))}
        {(jobs.data ?? []).map((job) => (
          <div className="data-row" key={job.id}>
            <span>
              <strong>{job.event_type}</strong>
              <small>{job.last_error ?? "Handler failed"}</small>
            </span>
            <span className="status-badge">{job.status}</span>
            <button
              className="button button-ghost"
              disabled={recover.isPending || reason.length < 20}
              onClick={() => recover.mutate(job.id)}
              type="button"
            >
              Recover
            </button>
          </div>
        ))}
      </div>
    );
  return (
    <div className="data-list">
      <h2>Purpose-limited exports</h2>
      {metrics.data?.suppressed ? (
        <div className="empty">
          Aggregate outcomes are suppressed for this cohort.
        </div>
      ) : null}
      {(exportsQuery.data ?? []).map((item: ExportJob) => (
        <div className="data-row" key={item.id}>
          <span>
            <strong>{item.purpose}</strong>
            <small>
              Expires {new Date(item.expires_at).toLocaleDateString()}
            </small>
          </span>
          <span className="status-badge">{item.status}</span>
        </div>
      ))}
      <form
        className="action-form"
        onSubmit={(event) => {
          event.preventDefault();
          requestExport.mutate();
        }}
      >
        <label>
          Export purpose
          <textarea
            required
            minLength={20}
            value={purpose}
            onChange={(event) => setPurpose(event.target.value)}
            rows={3}
          />
        </label>
        <button
          className="button button-primary"
          disabled={requestExport.isPending || purpose.length < 20}
          type="submit"
        >
          Request expiring export
        </button>
      </form>
    </div>
  );
}
