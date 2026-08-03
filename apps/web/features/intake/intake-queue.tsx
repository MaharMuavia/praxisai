"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { intakeQueueQuery } from "../../lib/queries/intake";

const statuses = [
  "",
  "NEW",
  "IN_REVIEW",
  "QUALIFIED",
  "REJECTED",
  "CONVERTED",
] as const;

function AccessState({ error }: { error: Error }) {
  const denied = /Request failed \((401|403)\)/.test(error.message);
  return (
    <div className="empty" role="alert">
      <strong>{denied ? "Permission denied" : "Unable to load intake"}</strong>
      <p>
        {denied
          ? "Your account does not have operations intake access."
          : "The intake service is unavailable. Try again shortly."}
      </p>
    </div>
  );
}

export function IntakeQueuePage() {
  const [status, setStatus] = useState("");
  const query = useQuery(intakeQueueQuery(status));
  if (query.isPending)
    return <div className="skeleton" aria-label="Loading intake queue" />;
  if (query.isError) return <AccessState error={query.error} />;
  return (
    <section className="panel" aria-labelledby="intake-queue-title">
      <div className="panel-header">
        <div>
          <h2 id="intake-queue-title">Human review queue</h2>
          <p>
            {query.data.length} submission{query.data.length === 1 ? "" : "s"}{" "}
            matching this filter.
          </p>
        </div>
        <label>
          Filter status
          <select
            aria-label="Filter intake status"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            {statuses.map((value) => (
              <option key={value} value={value}>
                {value || "All open records"}
              </option>
            ))}
          </select>
        </label>
      </div>
      {query.data.length === 0 ? (
        <div className="empty">No submissions match this filter.</div>
      ) : (
        <div className="data-list">
          {query.data.map((submission) => (
            <Link
              className="data-row"
              href={`/ops/intake/${submission.id}`}
              key={submission.id}
            >
              <span>
                <strong>
                  {String(submission.payload.full_name ?? "Unnamed contact")}
                </strong>
                <small>
                  {submission.kind.replace("_", " ")} ·{" "}
                  {submission.contact_email}
                </small>
              </span>
              <span>
                <strong>{submission.status}</strong>
                <small>
                  {new Date(submission.created_at).toLocaleString()}
                </small>
              </span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
