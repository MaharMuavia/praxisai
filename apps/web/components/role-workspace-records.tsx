import type { components } from "@praxisai/api-client";
import Link from "next/link";
import { MoneyAmount } from "./money-amount";

type Invoice = components["schemas"]["ClientInvoiceView"];
type Credential = components["schemas"]["StudentCredentialView"];
type Earnings = components["schemas"]["EarningsItemView"];
type LeadReview = components["schemas"]["LeadReviewQueueItem"];
type Approval = components["schemas"]["ApprovalQueueItem"];
type Risk = components["schemas"]["RiskQueueItem"];
type Offer = components["schemas"]["OfferView"];

export type RoleWorkspaceData =
  | { kind: "invoices"; items: Invoice[] | null }
  | { kind: "credentials"; items: Credential[] | null }
  | { kind: "earnings"; items: Earnings[] | null }
  | { kind: "reviews"; items: LeadReview[] | null }
  | { kind: "approvals"; items: Approval[] | null }
  | { kind: "risks"; items: Risk[] | null }
  | { kind: "offers"; items: Offer[] | null };

function EmptyRecords() {
  return <div className="empty">No authorized records require attention.</div>;
}

export function RoleWorkspaceRecords({
  data,
  onOfferDecision,
  submittingOfferId,
}: {
  data: RoleWorkspaceData;
  onOfferDecision?: (offerId: string, decision: "accept" | "decline") => void;
  submittingOfferId?: string | null;
}) {
  if (data.items === null) {
    return <div className="skeleton" aria-label="Loading workspace records" />;
  }
  if (data.items.length === 0) return <EmptyRecords />;

  if (data.kind === "offers") {
    return data.items.map((offer) => {
      const amount = offer.terms_snapshot.gross_compensation_minor;
      const currency = offer.terms_snapshot.currency;
      const compensation =
        typeof amount === "number" && typeof currency === "string" ? (
          <MoneyAmount amountMinor={amount} currency={currency} />
        ) : (
          "See terms"
        );
      return (
        <div className="data-row" key={offer.id}>
          <span>
            <Link href={`/student/projects/${offer.project_id}`}>
              <strong>{offer.role}</strong>
            </Link>
            <small>
              Expires {new Date(offer.expires_at).toLocaleDateString()} ·
              declining has no reputation penalty
            </small>
          </span>
          <span className="status-badge">{offer.state}</span>
          <span>
            <small>Gross compensation</small>
            <strong>{compensation}</strong>
          </span>
          {offer.state === "OFFERED" ? (
            <span className="row-actions">
              <button
                className="button button-primary"
                disabled={submittingOfferId === offer.id}
                onClick={() => onOfferDecision?.(offer.id, "accept")}
                type="button"
              >
                Accept
              </button>
              <button
                className="button button-ghost"
                disabled={submittingOfferId === offer.id}
                onClick={() => onOfferDecision?.(offer.id, "decline")}
                type="button"
              >
                Decline
              </button>
            </span>
          ) : (
            <span>•</span>
          )}
        </div>
      );
    });
  }

  if (data.kind === "invoices") {
    return data.items.map((invoice) => (
      <Link
        className="data-row"
        href={`/client/projects/${invoice.project_id}`}
        key={invoice.id}
      >
        <span>
          <strong>{invoice.number}</strong>
          <small>{invoice.project_title}</small>
        </span>
        <span className="status-badge">
          {invoice.status.replaceAll("_", " ")}
        </span>
        <span>
          <small>Recorded amount</small>
          <strong>
            <MoneyAmount
              amountMinor={invoice.amount_minor}
              currency={invoice.currency}
            />
          </strong>
        </span>
        <span aria-label={`${invoice.environment} environment`}>→</span>
      </Link>
    ));
  }

  if (data.kind === "credentials") {
    return data.items.map((credential) => (
      <Link
        className="data-row"
        href={`/verify/${credential.public_slug}`}
        key={credential.id}
      >
        <span>
          <strong>{credential.project_title}</strong>
          <small>
            Issued {new Date(credential.issued_at).toLocaleDateString()}
          </small>
        </span>
        <span className="status-badge">{credential.status}</span>
        <span>
          <small>Public verification</small>
          <strong>{credential.public_slug}</strong>
        </span>
        <span>→</span>
      </Link>
    ));
  }

  if (data.kind === "earnings") {
    return data.items.map((earning) => (
      <Link
        className="data-row"
        href={`/student/projects/${earning.project_id}`}
        key={earning.allocation_id}
      >
        <span>
          <strong>{earning.project_title}</strong>
          <small>
            {earning.failure_reason ?? "No payout exception recorded"}
          </small>
        </span>
        <span className="status-badge">
          {(earning.payout_status ?? earning.allocation_status).replaceAll(
            "_",
            " ",
          )}
        </span>
        <span>
          <small>Approved allocation</small>
          <strong>
            <MoneyAmount
              amountMinor={earning.amount_minor}
              currency={earning.currency}
            />
          </strong>
        </span>
        <span>→</span>
      </Link>
    ));
  }

  if (data.kind === "reviews") {
    return data.items.map((review) => (
      <Link
        className="data-row"
        href={`/lead/projects/${review.project_id}`}
        key={review.project_id}
      >
        <span>
          <strong>{review.project_title}</strong>
          <small>
            {review.latest_reviewed_at
              ? `Last reviewed ${new Date(review.latest_reviewed_at).toLocaleDateString()}`
              : "No review submitted"}
          </small>
        </span>
        <span className="status-badge">
          {review.project_state.replaceAll("_", " ")}
        </span>
        <span>
          <small>Recommendation</small>
          <strong>
            {review.latest_recommendation?.replaceAll("_", " ") ?? "Pending"}
          </strong>
        </span>
        <span>→</span>
      </Link>
    ));
  }

  if (data.kind === "approvals") {
    return data.items.map((approval) => (
      <Link
        className="data-row"
        href={`/ops/projects/${approval.project_id}`}
        key={approval.id}
      >
        <span>
          <strong>{approval.project_title}</strong>
          <small>{approval.subject_type.replaceAll("_", " ")}</small>
        </span>
        <span className="status-badge">{approval.decision}</span>
        <span>
          <small>Queue reason</small>
          <strong>{approval.reason ?? "Human decision required"}</strong>
        </span>
        <span>→</span>
      </Link>
    ));
  }

  return data.items.map((risk) => (
    <Link
      className="data-row"
      href={`/ops/projects/${risk.project_id}`}
      key={risk.id}
    >
      <span>
        <strong>{risk.project_title}</strong>
        <small>{risk.summary}</small>
      </span>
      <span className="status-badge">{risk.status}</span>
      <span>
        <small>Evidence source</small>
        <strong>
          {risk.source.replaceAll("_", " ")} · {risk.confidence}
        </strong>
      </span>
      <span>→</span>
    </Link>
  ));
}
