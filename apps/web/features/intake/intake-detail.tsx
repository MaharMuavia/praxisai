"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiBase } from "../../lib/api";
import {
  intakeDetailQuery,
  intakeKeys,
  type IntakeStatus,
} from "../../lib/queries/intake";

const nextStatuses: IntakeStatus[] = [
  "IN_REVIEW",
  "QUALIFIED",
  "REJECTED",
  "CONVERTED",
];

export function IntakeDetailPage({ submissionId }: { submissionId: string }) {
  const queryClient = useQueryClient();
  const query = useQuery(intakeDetailQuery(submissionId));
  const [status, setStatus] = useState<IntakeStatus | "">("");
  const [notes, setNotes] = useState("");
  const [reason, setReason] = useState("");
  const mutation = useMutation({
    mutationFn: async () => {
      if (!query.data || !status) throw new Error("Choose a next status");
      const response = await fetch(`${apiBase}/ops/intake/${submissionId}`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token":
            document.cookie.match(/praxis_csrf=([^;]+)/)?.[1] ?? "",
        },
        body: JSON.stringify({
          status,
          expected_version: query.data.version,
          qualification_notes: notes || undefined,
          rejection_reason: reason || undefined,
          conversion_evidence: notes || undefined,
          reopen_reason: reason || undefined,
        }),
      });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
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
  if (query.isPending)
    return <div className="skeleton" aria-label="Loading intake detail" />;
  if (query.isError)
    return (
      <div className="empty" role="alert">
        <strong>
          {/403/.test(query.error.message)
            ? "Permission denied"
            : "Intake record unavailable"}
        </strong>
        <p>Return to the queue and try again.</p>
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
            {submission.kind.replace("_", " ")} · {submission.contact_email} ·
            version {submission.version}
          </p>
        </div>
        <strong>{submission.status}</strong>
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
      {submission.status !== "CONVERTED" ? (
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
              <option value="">Choose a transition</option>
              {nextStatuses
                .filter((item) => item !== submission.status)
                .map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Review notes
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={4}
            />
          </label>
          <label>
            Reason / evidence
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={3}
            />
          </label>
          {mutation.isError ? (
            <div className="error" role="alert">
              {mutation.error.message}
            </div>
          ) : null}
          <button
            className="button button-primary"
            disabled={mutation.isPending}
            type="submit"
          >
            {mutation.isPending ? "Saving…" : "Save review"}
          </button>
        </form>
      ) : null}
    </section>
  );
}
