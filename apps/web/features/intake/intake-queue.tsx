"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
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
const kinds = ["", "company", "student", "expert_lead", "university"] as const;

function AccessState({ error }: { error: Error }) {
  const denied = /401|403|permission/i.test(error.message);
  return (
    <div className="empty" role="alert">
      <strong>{denied ? "Permission denied" : "Unable to load intake"}</strong>
      <p>
        {denied
          ? "Your account does not have operations intake access."
          : `${error.message} Try again shortly.`}
      </p>
    </div>
  );
}

export function IntakeQueuePage() {
  const [status, setStatus] = useState("");
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const [actionRequired, setActionRequired] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const params = useMemo(() => {
    const value = new URLSearchParams({ page_size: "50" });
    if (status) value.set("status", status);
    if (kind) value.set("kind", kind);
    if (search.trim()) value.set("search", search.trim());
    if (actionRequired) value.set("action_required", "true");
    if (cursor) value.set("cursor", cursor);
    return value;
  }, [actionRequired, cursor, kind, search, status]);
  const query = useQuery(intakeQueueQuery(params));
  if (query.isPending)
    return <div className="skeleton" aria-label="Loading intake queue" />;
  if (query.isError) return <AccessState error={query.error} />;
  return (
    <section className="panel" aria-labelledby="intake-queue-title">
      <div className="panel-header">
        <div>
          <h2 id="intake-queue-title">Human review queue</h2>
          <p>
            {query.data.items.length} privacy-safe summary records on this page.
          </p>
        </div>
        <div className="public-intake-grid">
          <label>
            Status
            <select
              aria-label="Filter intake status"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setCursor(null);
              }}
            >
              {statuses.map((value) => (
                <option key={value} value={value}>
                  {value || "All statuses"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Type
            <select
              aria-label="Filter intake kind"
              value={kind}
              onChange={(event) => {
                setKind(event.target.value);
                setCursor(null);
              }}
            >
              {kinds.map((value) => (
                <option key={value} value={value}>
                  {value || "All types"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Search
            <input
              aria-label="Search intake"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setCursor(null);
              }}
              placeholder="Name, source, campaign"
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={actionRequired}
              onChange={(event) => {
                setActionRequired(event.target.checked);
                setCursor(null);
              }}
            />{" "}
            Action required
          </label>
        </div>
      </div>
      {query.data.items.length === 0 ? (
        <div className="empty">No submissions match this filter.</div>
      ) : (
        <div className="data-list">
          {query.data.items.map((submission) => (
            <Link
              className="data-row"
              href={`/ops/intake/${submission.id}`}
              key={submission.id}
            >
              <span>
                <strong>{submission.display_name}</strong>
                <small>
                  {submission.kind.replace("_", " ")} ·{" "}
                  {submission.source ?? "Direct"}
                </small>
              </span>
              <span>
                <strong>{submission.status}</strong>
                <small>
                  {new Date(submission.created_at).toLocaleString()}
                </small>
              </span>
              {submission.action_required ? (
                <span className="status-badge">Needs review</span>
              ) : null}
            </Link>
          ))}
        </div>
      )}
      {query.data.next_cursor ? (
        <button
          className="button button-ghost"
          type="button"
          onClick={() => setCursor(query.data.next_cursor)}
        >
          Next page
        </button>
      ) : null}
    </section>
  );
}
