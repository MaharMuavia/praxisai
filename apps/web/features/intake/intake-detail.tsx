"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiBase } from "../../lib/api";
import { parseApiError } from "../../lib/queries/shared";
import {
  intakeAuditQuery,
  intakeDetailQuery,
  intakeKeys,
  intakeOwnersQuery,
  type IntakeStatus,
} from "../../lib/queries/intake";

const labels: Record<IntakeStatus, string> = {
  NEW: "New",
  IN_REVIEW: "In review",
  QUALIFIED: "Qualified",
  REJECTED: "Rejected",
  CONVERTED: "Converted",
};

export function IntakeDetailPage({ submissionId }: { submissionId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery(intakeDetailQuery(submissionId));
  const owners = useQuery(intakeOwnersQuery());
  const audit = useQuery(intakeAuditQuery(submissionId));
  const [status, setStatus] = useState<IntakeStatus | "">("");
  const [ownerId, setOwnerId] = useState("");
  const [notes, setNotes] = useState("");
  const [reason, setReason] = useState("");
  const mutation = useMutation({
    mutationFn: async () => {
      if (!query.data || !status) throw new Error("Choose a valid transition");
      const payload: Record<string, unknown> = {
        status,
        owner_id: ownerId || null,
        expected_version: query.data.version,
      };
      if (status === "QUALIFIED") payload.qualification_notes = notes;
      if (status === "REJECTED") payload.rejection_reason = reason;
      if (status === "CONVERTED") payload.conversion_evidence = notes;
      if (query.data.status === "REJECTED" && status === "IN_REVIEW")
        payload.reopen_reason = reason;
      const response = await fetch(`${apiBase}/ops/intake/${submissionId}`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token":
            document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw await parseApiError(response);
      return response.json();
    },
    onSuccess: async (updated) => {
      queryClient.setQueryData(intakeKeys.detail(submissionId), updated);
      await queryClient.invalidateQueries({ queryKey: intakeKeys.all });
      setStatus("");
      setNotes("");
      setReason("");
    },
  });
  const privacyMutation = useMutation({
    mutationFn: async (action: "anonymize" | "withdraw") => {
      const response = await fetch(
        `${apiBase}/ops/intake/${submissionId}/${action}`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token":
              document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
          },
          body:
            action === "withdraw"
              ? JSON.stringify({
                  reason: "Operator requested privacy withdrawal review.",
                })
              : undefined,
        },
      );
      if (!response.ok) throw await parseApiError(response);
      return response.status === 204 ? null : response.json();
    },
    onSuccess: (updated) => {
      if (updated)
        queryClient.setQueryData(intakeKeys.detail(submissionId), updated);
      void queryClient.invalidateQueries({ queryKey: intakeKeys.all });
    },
  });
  if (query.isPending)
    return <div className="skeleton" aria-label="Loading intake detail" />;
  if (query.isError)
    return (
      <div className="empty" role="alert">
        <strong>
          {/401|403|permission/i.test(query.error.message)
            ? "Permission denied"
            : "Intake record unavailable"}
        </strong>
        <p>{query.error.message}</p>
        <Link className="button button-ghost" href="/ops/intake">
          Back to queue
        </Link>
      </div>
    );
  const submission = query.data;
  return (
    <section className="panel" aria-labelledby="intake-detail-title">
      <div className="panel-header">
        <div>
          <Link href="/ops/intake">← Back to queue</Link>
          <h2 id="intake-detail-title">
            {String(submission.payload.full_name ?? "Unnamed contact")}
          </h2>
          <p>
            {submission.kind.replace("_", " ")} ·{" "}
            {submission.contact_email ?? "Contact redacted"} · version{" "}
            {submission.version}
          </p>
        </div>
        <strong>{labels[submission.status]}</strong>
      </div>
      <div className="data-list">
        {Object.entries(submission.payload)
          .filter(([key]) => key !== "full_name")
          .map(([key, value]) => (
            <div className="data-row" key={key}>
              <span>
                <strong>{key.replaceAll("_", " ")}</strong>
              </span>
              <span>{String(value)}</span>
            </div>
          ))}
      </div>
      {submission.allowed_transitions.length > 0 ? (
        <form
          className="panel-form"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
        >
          <label>
            Next status
            <select
              required
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as IntakeStatus)
              }
            >
              <option value="">Choose a valid transition</option>
              {submission.allowed_transitions.map((value) => (
                <option key={value} value={value}>
                  {labels[value]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Owner
            <select
              value={ownerId || submission.owner_id || ""}
              onChange={(event) => setOwnerId(event.target.value)}
            >
              <option value="">Unassigned</option>
              {(owners.data ?? []).map((owner) => (
                <option key={owner.id} value={owner.id}>
                  {owner.display_name}
                </option>
              ))}
            </select>
          </label>
          {status === "QUALIFIED" || status === "CONVERTED" ? (
            <label>
              {status === "QUALIFIED"
                ? "Qualification notes"
                : "Conversion evidence"}
              <textarea
                required
                minLength={10}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={4}
              />
            </label>
          ) : null}
          {status === "REJECTED" ||
          (submission.status === "REJECTED" && status === "IN_REVIEW") ? (
            <label>
              {status === "REJECTED" ? "Rejection reason" : "Reopen reason"}
              <textarea
                required
                minLength={10}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={3}
              />
            </label>
          ) : null}
          {mutation.isError ? (
            <div className="error" role="alert">
              {mutation.error.message}
              {(mutation.error as { status?: number }).status === 409 ? (
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={() => void query.refetch()}
                >
                  Reload latest record
                </button>
              ) : null}
            </div>
          ) : null}
          <button
            className="button button-primary"
            disabled={mutation.isPending || !status}
            type="submit"
          >
            {mutation.isPending ? "Saving…" : "Save review"}
          </button>
        </form>
      ) : (
        <div className="empty">This record is terminal for review actions.</div>
      )}
      <div className="panel-header">
        <h3>Privacy actions</h3>
        <div>
          <button
            className="button button-ghost"
            disabled={
              privacyMutation.isPending || Boolean(submission.anonymized_at)
            }
            onClick={() => privacyMutation.mutate("withdraw")}
            type="button"
          >
            Request withdrawal
          </button>
          <button
            className="button button-ghost"
            disabled={
              privacyMutation.isPending || Boolean(submission.anonymized_at)
            }
            onClick={() => privacyMutation.mutate("anonymize")}
            type="button"
          >
            Anonymize now
          </button>
        </div>
      </div>
      <div className="data-list">
        <h3>Audit timeline</h3>
        {audit.data?.map((event) => (
          <div className="data-row" key={event.id}>
            <span>
              <strong>{event.action}</strong>
              <small>{new Date(event.created_at).toLocaleString()}</small>
            </span>
            <span>{event.correlation_id}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
