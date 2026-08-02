"use client";

import { praxisFetch, type components } from "@praxisai/api-client";
import { type FormEvent, useState } from "react";
import { MoneyAmount } from "./money-amount";

type ProjectWorkspace = components["schemas"]["ProjectWorkspaceView"];
type Project = components["schemas"]["ProjectView"];
type AgentRun = components["schemas"]["AgentRunView"];
type QuoteResult = components["schemas"]["QuoteResult"];

const apiBase =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function StateLabel({ value }: { value: string }) {
  return <span className="status-badge">{value.replaceAll("_", " ")}</span>;
}

function snapshotText(snapshot: Record<string, unknown>, key: string) {
  const value = snapshot[key];
  return typeof value === "string" ? value : null;
}

function snapshotList(snapshot: Record<string, unknown>, key: string) {
  const value = snapshot[key];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function planMilestones(snapshot: Record<string, unknown>) {
  const milestones = snapshot.milestones;
  if (!Array.isArray(milestones)) return [];
  return milestones.flatMap((milestone) => {
    if (typeof milestone !== "object" || milestone === null) return [];
    const title = "title" in milestone ? milestone.title : null;
    const tasks = "tasks" in milestone ? milestone.tasks : null;
    if (typeof title !== "string" || !Array.isArray(tasks)) return [];
    return [
      {
        title,
        tasks: tasks.flatMap((task) => {
          if (typeof task !== "object" || task === null || !("title" in task)) {
            return [];
          }
          return typeof task.title === "string" ? [task.title] : [];
        }),
      },
    ];
  });
}

export function ProjectCommandCenter({
  workspace,
  role,
  onWorkspaceChange,
}: {
  workspace: ProjectWorkspace;
  role: string;
  onWorkspaceChange: (workspace: ProjectWorkspace) => void;
}) {
  const { project } = workspace;
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [offerRole, setOfferRole] = useState<"student" | "technical lead">(
    "student",
  );
  const scope = workspace.latest_scope;
  const quote = workspace.latest_quote;
  const effortLow = scope ? Number(scope.snapshot.effort_low_hours ?? 1) : 1;
  const effortHigh = scope
    ? Number(scope.snapshot.effort_high_hours ?? effortLow)
    : effortLow;

  async function refreshWorkspace() {
    const updated = await praxisFetch<ProjectWorkspace>(
      apiBase,
      `/projects/${project.id}/workspace`,
    );
    onWorkspaceChange(updated);
  }

  async function transitionProject(
    target: string,
    reason: string,
    notice: string,
  ) {
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<Project>(
        apiBase,
        `/projects/${project.id}/transition`,
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({
            to_state: target,
            reason,
            expected_version: project.version,
          }),
        },
      );
      await refreshWorkspace();
      setActionNotice(notice);
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Project action failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function generateScope() {
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<AgentRun>(
        apiBase,
        `/projects/${project.id}/scope-runs`,
        { method: "POST" },
      );
      await refreshWorkspace();
      setActionNotice(
        "The scope proposal is ready for human review. No project terms were accepted automatically.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Scope generation failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function createQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const dollarsToMinor = (name: string) =>
      Math.round(Number(form.get(name)) * 100);
    const percentToBasisPoints = (name: string) =>
      Math.round(Number(form.get(name)) * 100);
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<QuoteResult>(
        apiBase,
        `/projects/${project.id}/quotes`,
        {
          method: "POST",
          body: JSON.stringify({
            student_hours_low: Number(form.get("studentHoursLow")),
            student_hours_base: Number(form.get("studentHoursBase")),
            student_hours_high: Number(form.get("studentHoursHigh")),
            student_rate_minor: dollarsToMinor("studentRate"),
            lead_hours: Number(form.get("leadHours")),
            lead_rate_minor: dollarsToMinor("leadRate"),
            platform_fee_basis_points: percentToBasisPoints("platformFee"),
            risk_multiplier_basis_points:
              percentToBasisPoints("riskMultiplier"),
            tax_basis_points: percentToBasisPoints("tax"),
            currency: project.currency,
            revision_rounds: Number(form.get("revisionRounds")),
          }),
        },
      );
      await refreshWorkspace();
      setActionNotice(
        "The deterministic quote snapshot is ready for coordinator approval.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Quote creation failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function recordExternalFunding(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<void>(
        apiBase,
        `/ops/projects/${project.id}/external-funding`,
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({
            amount_minor: Math.round(Number(form.get("fundingAmount")) * 100),
            currency: project.currency,
            evidence_reference: String(form.get("evidenceReference")),
            approved_arrangement: form.get("approvedArrangement") === "on",
          }),
        },
      );
      await refreshWorkspace();
      setActionNotice(
        "External funding evidence was recorded in the balanced ledger. No payment provider was called.",
      );
      formElement.reset();
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Funding evidence failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function runStaffingMatch() {
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<{ candidate_count: number }>(
        apiBase,
        `/projects/${project.id}/staffing-runs`,
        { method: "POST" },
      );
      await refreshWorkspace();
      setActionNotice(
        "Deterministic eligibility and matching evidence is ready for coordinator review.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Staffing match failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function createAssignmentOffer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<components["schemas"]["OfferView"]>(
        apiBase,
        `/projects/${project.id}/assignment-offers`,
        {
          method: "POST",
          body: JSON.stringify({
            recipient_user_id: String(form.get("recipientUserId")),
            role: offerRole,
            role_title: String(form.get("roleTitle")),
            gross_compensation_minor: Math.round(
              Number(form.get("grossCompensation")) * 100,
            ),
            currency: project.currency,
            expected_hours_low: Number(form.get("offerHoursLow")),
            expected_hours_high: Number(form.get("offerHoursHigh")),
            expected_weekly_hours: Number(form.get("weeklyHours")),
            deadline: new Date(String(form.get("offerDeadline"))).toISOString(),
            revision_rounds: Number(form.get("offerRevisions")),
            portfolio_terms: String(form.get("portfolioTerms")),
            expires_at: new Date(
              String(form.get("offerExpires")),
            ).toISOString(),
            conflict_declared: false,
          }),
        },
      );
      await refreshWorkspace();
      setActionNotice(
        "Immutable offer terms were sent. Declining or expiry has no reputation impact.",
      );
      formElement.reset();
      setOfferRole("student");
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Offer creation failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function runPlanProposal() {
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<components["schemas"]["PlanRunView"]>(
        apiBase,
        `/projects/${project.id}/plan-runs`,
        { method: "POST" },
      );
      await refreshWorkspace();
      setActionNotice(
        "The plan proposal covers the accepted criteria and is awaiting coordinator approval.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Plan generation failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function approvePlan() {
    if (workspace.latest_plan === null) return;
    setIsSubmitting(true);
    setActionError(null);
    setActionNotice(null);
    try {
      await praxisFetch<components["schemas"]["PlanRunView"]>(
        apiBase,
        `/projects/${project.id}/plans/${workspace.latest_plan.id}/coordinator-decision`,
        {
          method: "POST",
          body: JSON.stringify({
            decision: "APPROVED",
            reason:
              "Coordinator verified criterion coverage, dependencies, estimates, and milestones.",
          }),
        },
      );
      await refreshWorkspace();
      setActionNotice("The project plan was approved and tasks were created.");
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Plan approval failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="command-center">
      <div className="data-row">
        <span>
          <strong>{project.title}</strong>
          <small>{project.description}</small>
        </span>
        <StateLabel value={project.state} />
        <span>
          <small>External funding evidence</small>
          <strong>
            <MoneyAmount
              amountMinor={project.funded_minor}
              currency={project.currency}
            />{" "}
            of{" "}
            <MoneyAmount
              amountMinor={project.required_deposit_minor}
              currency={project.currency}
            />
          </strong>
        </span>
        <span>{project.is_demo ? "Demo" : "Live"}</span>
      </div>

      <div className="lifecycle-actions" aria-label="Project lifecycle actions">
        {role === "client_owner" && project.state === "DRAFT" && (
          <button
            className="button button-primary"
            disabled={isSubmitting}
            onClick={() =>
              void transitionProject(
                "SCOPING",
                "Client submitted the intake for scope proposal generation.",
                "Project submitted for scoping.",
              )
            }
            type="button"
          >
            Submit for scoping
          </button>
        )}
        {["client_owner", "coordinator", "platform_admin"].includes(role) &&
          project.state === "SCOPING" &&
          scope === null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() => void generateScope()}
              type="button"
            >
              Generate scope proposal
            </button>
          )}
        {["coordinator", "platform_admin"].includes(role) &&
          project.state === "SCOPING" &&
          scope !== null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "AWAITING_COORDINATOR_SCOPE_APPROVAL",
                  "Generated scope proposal sent to the coordinator approval queue.",
                  "Scope proposal sent to the coordinator queue.",
                )
              }
              type="button"
            >
              Send scope to approval queue
            </button>
          )}
        {role === "coordinator" &&
          project.state === "AWAITING_COORDINATOR_SCOPE_APPROVAL" &&
          quote !== null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "AWAITING_CLIENT_SCOPE_APPROVAL",
                  "Coordinator approved the proposed scope and deterministic quote.",
                  "Scope and quote sent to the client for acceptance.",
                )
              }
              type="button"
            >
              Approve scope and quote
            </button>
          )}
        {["coordinator", "technical_lead"].includes(role) &&
          project.state === "READY_TO_START" &&
          workspace.latest_plan === null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() => void runPlanProposal()}
              type="button"
            >
              Generate plan proposal
            </button>
          )}
        {role === "coordinator" &&
          project.state === "READY_TO_START" &&
          workspace.latest_plan?.status === "PROPOSED" && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() => void approvePlan()}
              type="button"
            >
              Approve project plan
            </button>
          )}
        {["coordinator", "technical_lead"].includes(role) &&
          project.state === "READY_TO_START" &&
          workspace.latest_plan?.status === "APPROVED" && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "ACTIVE",
                  "Approved project plan activated for the accepted and funded team.",
                  "Project is active. Approved tasks are ready for execution.",
                )
              }
              type="button"
            >
              Activate approved plan
            </button>
          )}
        {role === "coordinator" &&
          project.state === "STAFFING" &&
          workspace.latest_staffing === null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() => void runStaffingMatch()}
              type="button"
            >
              Run staffing match
            </button>
          )}
        {role === "coordinator" &&
          project.state === "STAFFING" &&
          workspace.latest_staffing !== null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "AWAITING_STAFFING_APPROVAL",
                  "Coordinator submitted deterministic staffing evidence for approval.",
                  "Staffing evidence moved to the approval gate.",
                )
              }
              type="button"
            >
              Send staffing match to approval
            </button>
          )}
        {role === "coordinator" &&
          project.state === "AWAITING_STAFFING_APPROVAL" &&
          workspace.latest_staffing !== null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "AWAITING_STUDENT_ACCEPTANCE",
                  "Coordinator approved the staffing evidence for offer preparation.",
                  "Staffing approved. Assignment offers can now be prepared.",
                )
              }
              type="button"
            >
              Approve staffing match
            </button>
          )}
        {role === "coordinator" &&
          project.state === "AWAITING_STUDENT_ACCEPTANCE" &&
          workspace.assignment_offers.length > 0 &&
          workspace.assignment_offers.every(
            (offer) => !["DRAFT", "OFFERED"].includes(offer.state),
          ) && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "READY_TO_START",
                  "Coordinator verified that all required offers were decided and accepted.",
                  "The accepted team is ready for project planning.",
                )
              }
              type="button"
            >
              Confirm accepted team
            </button>
          )}
        {role === "client_owner" &&
          project.state === "AWAITING_CLIENT_SCOPE_APPROVAL" &&
          quote !== null && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "AWAITING_DEPOSIT",
                  "Client accepted the immutable scope and quote snapshots.",
                  "Scope and quote accepted. External funding evidence is now required.",
                )
              }
              type="button"
            >
              Accept scope and quote
            </button>
          )}
        {role === "coordinator" &&
          project.state === "AWAITING_DEPOSIT" &&
          project.funded_minor >= project.required_deposit_minor && (
            <button
              className="button button-primary"
              disabled={isSubmitting}
              onClick={() =>
                void transitionProject(
                  "STAFFING",
                  "Coordinator verified that approved external funding covers the required deposit.",
                  "Funding guard satisfied. Project moved to staffing.",
                )
              }
              type="button"
            >
              Confirm funding and start staffing
            </button>
          )}
        {isSubmitting && <span role="status">Saving audited action…</span>}
      </div>
      {actionError && <div className="error">{actionError}</div>}
      {actionNotice && <div className="notice">{actionNotice}</div>}

      {role === "coordinator" &&
        project.state === "AWAITING_DEPOSIT" &&
        project.funded_minor < project.required_deposit_minor && (
          <form className="quote-form" onSubmit={recordExternalFunding}>
            <h3>Record external funding evidence</h3>
            <p>
              Stripe is disabled. Record only an approved off-platform funding
              arrangement; this creates balanced ledger evidence without moving
              money.
            </p>
            <div className="form-grid">
              <label>
                Amount ({project.currency})
                <input
                  defaultValue={(
                    (project.required_deposit_minor - project.funded_minor) /
                    100
                  ).toFixed(2)}
                  min="0.01"
                  name="fundingAmount"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Evidence reference
                <input
                  minLength={5}
                  name="evidenceReference"
                  placeholder="Bank receipt or approved agreement reference"
                  required
                  type="text"
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input name="approvedArrangement" required type="checkbox" />I
              verified this is an approved external funding arrangement.
            </label>
            <button
              className="button button-primary"
              disabled={isSubmitting}
              type="submit"
            >
              Record funding evidence
            </button>
          </form>
        )}

      <h3 className="section-label">Scope proposal</h3>
      {scope === null ? (
        <div className="empty compact-empty">
          No scope proposal exists. AI output is a proposal and cannot approve
          itself.
        </div>
      ) : (
        <div className="evidence-card">
          <div className="evidence-card-heading">
            <span>
              <strong>
                {snapshotText(scope.snapshot, "normalized_title") ??
                  project.title}
              </strong>
              <small>Scope version {scope.version}</small>
            </span>
            <StateLabel value={scope.status} />
          </div>
          <p>{snapshotText(scope.snapshot, "summary")}</p>
          <div className="scope-columns">
            <div>
              <strong>Deliverables</strong>
              <ul>
                {snapshotList(scope.snapshot, "deliverables").map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Acceptance criteria</strong>
              <ol>
                {scope.acceptance_criteria.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            </div>
          </div>
          <small>
            Proposed effort: {effortLow}–{effortHigh} hours · Complexity:{" "}
            {snapshotText(scope.snapshot, "complexity") ?? "pending review"}
          </small>
        </div>
      )}

      {role === "coordinator" &&
        project.state === "AWAITING_COORDINATOR_SCOPE_APPROVAL" &&
        quote === null &&
        scope !== null && (
          <form className="quote-form" onSubmit={createQuote}>
            <h3>Build deterministic quote</h3>
            <p>
              Confirm hours and commercial inputs. Amounts are calculated on the
              server using integer minor units.
            </p>
            <div className="form-grid three-column-grid">
              <label>
                Low student hours
                <input
                  defaultValue={effortLow}
                  min="1"
                  name="studentHoursLow"
                  required
                  type="number"
                />
              </label>
              <label>
                Base student hours
                <input
                  defaultValue={Math.round((effortLow + effortHigh) / 2)}
                  min="1"
                  name="studentHoursBase"
                  required
                  type="number"
                />
              </label>
              <label>
                High student hours
                <input
                  defaultValue={effortHigh}
                  min="1"
                  name="studentHoursHigh"
                  required
                  type="number"
                />
              </label>
              <label>
                Student rate ({project.currency}/hour)
                <input
                  min="0.01"
                  name="studentRate"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Lead hours
                <input
                  defaultValue="0"
                  min="0"
                  name="leadHours"
                  required
                  type="number"
                />
              </label>
              <label>
                Lead rate ({project.currency}/hour)
                <input
                  defaultValue="0"
                  min="0"
                  name="leadRate"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Platform fee (%)
                <input
                  defaultValue="0"
                  max="50"
                  min="0"
                  name="platformFee"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Risk multiplier (%)
                <input
                  defaultValue="100"
                  max="150"
                  min="100"
                  name="riskMultiplier"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Tax (%)
                <input
                  defaultValue="0"
                  max="50"
                  min="0"
                  name="tax"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                Included revisions
                <input
                  defaultValue="2"
                  max="5"
                  min="0"
                  name="revisionRounds"
                  required
                  type="number"
                />
              </label>
            </div>
            <button
              className="button button-primary"
              disabled={isSubmitting}
              type="submit"
            >
              Calculate and save quote
            </button>
          </form>
        )}

      <h3 className="section-label">Quote snapshot</h3>
      {quote === null ? (
        <div className="empty compact-empty">No quote has been recorded.</div>
      ) : (
        <div className="evidence-card">
          <div className="evidence-card-heading">
            <span>
              <strong>
                <MoneyAmount
                  amountMinor={quote.base_minor}
                  currency={quote.currency}
                />
              </strong>
              <small>
                Range{" "}
                <MoneyAmount
                  amountMinor={quote.low_minor}
                  currency={quote.currency}
                />
                –
                <MoneyAmount
                  amountMinor={quote.high_minor}
                  currency={quote.currency}
                />
              </small>
            </span>
            <StateLabel value={quote.status} />
          </div>
          {quote.line_items.map((item) => (
            <div className="quote-line" key={item.kind}>
              <span>{item.description}</span>
              <MoneyAmount
                amountMinor={item.amount_minor}
                currency={quote.currency}
              />
            </div>
          ))}
          <small>
            Quote version {quote.version} · {quote.revision_rounds} included
            revisions · {quote.formula_version}
          </small>
        </div>
      )}

      {workspace.latest_staffing !== null && (
        <>
          <h3 className="section-label">Staffing evidence</h3>
          <div className="evidence-card">
            <div className="evidence-card-heading">
              <span>
                <strong>Deterministic candidate ranking</strong>
                <small>
                  Weights {workspace.latest_staffing.weights_version}
                </small>
              </span>
              <StateLabel value={workspace.latest_staffing.status} />
            </div>
            {workspace.latest_staffing.candidates.length === 0 ? (
              <div className="empty compact-empty">
                No eligible candidates matched the approved constraints.
              </div>
            ) : (
              workspace.latest_staffing.candidates.map((candidate) => (
                <div
                  className="candidate-row"
                  key={candidate.student_profile_id}
                >
                  <span>
                    <strong>{candidate.display_name}</strong>
                    <small>{candidate.explanation}</small>
                  </span>
                  <span>
                    {(candidate.score_basis_points / 100).toFixed(2)}%
                  </span>
                  <StateLabel value={`${candidate.confidence} confidence`} />
                </div>
              ))
            )}
          </div>
        </>
      )}

      {role === "coordinator" &&
        project.state === "AWAITING_STUDENT_ACCEPTANCE" && (
          <>
            <h3 className="section-label">Assignment offers</h3>
            {workspace.assignment_offers.map((offer) => (
              <div className="data-row" key={offer.id}>
                <span>
                  <strong>{offer.recipient_display_name}</strong>
                  <small>{offer.role}</small>
                </span>
                <StateLabel value={offer.state} />
                <span>
                  <small>Expires</small>
                  <strong>{new Date(offer.expires_at).toLocaleString()}</strong>
                </span>
                <span>
                  {offer.state === "DECLINED"
                    ? "No reputation impact"
                    : "Terms preserved"}
                </span>
              </div>
            ))}
            <form className="quote-form" onSubmit={createAssignmentOffer}>
              <h3>Prepare immutable offer</h3>
              <p>
                Compensation, workload, deadline, revisions, and portfolio terms
                are snapshotted when the offer is sent.
              </p>
              <div className="form-grid three-column-grid">
                <label>
                  Assignment type
                  <select
                    name="offerRole"
                    onChange={(event) =>
                      setOfferRole(
                        event.target.value as "student" | "technical lead",
                      )
                    }
                    value={offerRole}
                  >
                    <option value="student">Student</option>
                    <option value="technical lead">Technical lead</option>
                  </select>
                </label>
                <label>
                  Recipient
                  <select name="recipientUserId" required>
                    <option value="">Select eligible person</option>
                    {offerRole === "student"
                      ? (workspace.latest_staffing?.candidates ?? []).map(
                          (candidate) => (
                            <option
                              key={candidate.student_user_id}
                              value={candidate.student_user_id}
                            >
                              {candidate.display_name}
                            </option>
                          ),
                        )
                      : workspace.eligible_leads.map((lead) => (
                          <option key={lead.user_id} value={lead.user_id}>
                            {lead.display_name} · {lead.available_hours}h
                            available
                          </option>
                        ))}
                  </select>
                </label>
                <label>
                  Role title
                  <input minLength={2} name="roleTitle" required type="text" />
                </label>
                <label>
                  Gross compensation ({project.currency})
                  <input
                    min="0.01"
                    name="grossCompensation"
                    required
                    step="0.01"
                    type="number"
                  />
                </label>
                <label>
                  Expected hours, low
                  <input min="1" name="offerHoursLow" required type="number" />
                </label>
                <label>
                  Expected hours, high
                  <input min="1" name="offerHoursHigh" required type="number" />
                </label>
                <label>
                  Weekly hours
                  <input
                    max="40"
                    min="1"
                    name="weeklyHours"
                    required
                    type="number"
                  />
                </label>
                <label>
                  Delivery deadline
                  <input name="offerDeadline" required type="datetime-local" />
                </label>
                <label>
                  Offer expires
                  <input name="offerExpires" required type="datetime-local" />
                </label>
                <label>
                  Included revisions
                  <input
                    defaultValue={quote?.revision_rounds ?? 2}
                    max="5"
                    min="0"
                    name="offerRevisions"
                    required
                    type="number"
                  />
                </label>
                <label>
                  Portfolio terms
                  <input
                    minLength={5}
                    name="portfolioTerms"
                    placeholder="Allowed after client approval"
                    required
                    type="text"
                  />
                </label>
              </div>
              <button
                className="button button-primary"
                disabled={isSubmitting}
                type="submit"
              >
                Send offer
              </button>
            </form>
          </>
        )}

      {workspace.latest_plan !== null && (
        <>
          <h3 className="section-label">Project plan</h3>
          <div className="evidence-card">
            <div className="evidence-card-heading">
              <span>
                <strong>Criteria-bound execution plan</strong>
                <small>
                  Project version{" "}
                  {String(workspace.latest_plan.plan_snapshot.project_version)}
                </small>
              </span>
              <StateLabel value={workspace.latest_plan.status} />
            </div>
            <div className="scope-columns">
              {planMilestones(workspace.latest_plan.plan_snapshot).map(
                (milestone) => (
                  <div key={milestone.title}>
                    <strong>{milestone.title}</strong>
                    <ul>
                      {milestone.tasks.map((task) => (
                        <li key={task}>{task}</li>
                      ))}
                    </ul>
                  </div>
                ),
              )}
            </div>
          </div>
        </>
      )}

      <h3 className="section-label">Tasks</h3>
      {workspace.tasks.length === 0 ? (
        <div className="empty compact-empty">
          No tasks have been approved for this project.
        </div>
      ) : (
        workspace.tasks.map((task) => (
          <div className="data-row" key={task.id}>
            <span>
              <strong>{task.title}</strong>
              <small>{task.definition_of_done}</small>
            </span>
            <StateLabel value={task.state} />
            <span>
              <small>Estimate</small>
              <strong>{task.estimate_hours} hours</strong>
            </span>
            <span>{task.assignee_id ? "Assigned" : "Unassigned"}</span>
          </div>
        ))
      )}

      <h3 className="section-label">Immutable delivery evidence</h3>
      {workspace.deliverables.length === 0 ? (
        <div className="empty compact-empty">
          No deliverable evidence has been submitted.
        </div>
      ) : (
        workspace.deliverables.map((deliverable) => (
          <div className="data-row" key={deliverable.id}>
            <span>
              <strong>{deliverable.title}</strong>
              <small>
                Version {deliverable.version}
                {deliverable.artifact_content_hash
                  ? ` · hash ${deliverable.artifact_content_hash.slice(0, 12)}…`
                  : " · no artifact"}
              </small>
            </span>
            <StateLabel value={deliverable.status} />
            <span>
              <small>QA / lead / client</small>
              <strong>
                {deliverable.qa_recommendation ?? "Pending"} /{" "}
                {deliverable.lead_recommendation ?? "Pending"} /{" "}
                {deliverable.client_decision ?? "Pending"}
              </strong>
            </span>
            <span>{deliverable.scan_status ?? "Not scanned"}</span>
          </div>
        ))
      )}

      <h3 className="section-label">Risk and audit trail</h3>
      {workspace.risks.map((risk) => (
        <div className="data-row" key={risk.id}>
          <span>
            <strong>{risk.summary}</strong>
            <small>{risk.source.replaceAll("_", " ")} evidence</small>
          </span>
          <StateLabel value={risk.status} />
          <span>
            <small>Confidence</small>
            <strong>{risk.confidence}</strong>
          </span>
          <span>{risk.human_decision ?? "Human review pending"}</span>
        </div>
      ))}
      {workspace.timeline.map((item) => (
        <div className="data-row" key={item.id}>
          <span>
            <strong>{item.reason}</strong>
            <small>{new Date(item.created_at).toLocaleString()}</small>
          </span>
          <StateLabel value={item.new_state} />
          <span>
            <small>Previous state</small>
            <strong>{item.previous_state.replaceAll("_", " ")}</strong>
          </span>
          <span>Audited</span>
        </div>
      ))}
      {workspace.risks.length === 0 && workspace.timeline.length === 0 && (
        <div className="empty compact-empty">
          No risk or transition evidence recorded.
        </div>
      )}
    </div>
  );
}
