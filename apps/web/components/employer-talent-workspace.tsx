"use client";

import { praxisFetch, type components } from "@praxisai/api-client";
import {
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  Clock3,
  FileSearch,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { demoWorkspaceSnapshot, withDemoFallback } from "../lib/demo-data";
import { MoneyAmount } from "./money-amount";
import { apiBase } from "../lib/api";

type EmployerOpportunity = components["schemas"]["EmployerOpportunityView"];
type Proposal = components["schemas"]["StudentProposalView"];
type Project = components["schemas"]["ProjectView"];

type PageKind = "home" | "proposals" | "publish";

export function EmployerTalentWorkspace({ page }: { page: PageKind }) {
  const [opportunities, setOpportunities] = useState<
    EmployerOpportunity[] | null
  >(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [decisionReasons, setDecisionReasons] = useState<
    Record<string, string>
  >({});
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoPreview, setIsDemoPreview] = useState(false);
  const [proposalQuery, setProposalQuery] = useState("");

  async function load() {
    const result = await withDemoFallback(
      Promise.all([
        praxisFetch<EmployerOpportunity[]>(
          apiBase,
          "/talent/employers/me/opportunities",
        ),
        praxisFetch<{ items: Project[] }>(apiBase, "/projects"),
      ]),
      [
        demoWorkspaceSnapshot.employerOpportunities,
        { items: demoWorkspaceSnapshot.projects },
      ] as [EmployerOpportunity[], { items: Project[] }],
    );
    const [nextOpportunities, projectList] = result.data;
    setOpportunities(nextOpportunities);
    setProjects(projectList.items);
    setIsDemoPreview(result.isDemo);
  }

  useEffect(() => {
    void load().catch((reason: unknown) =>
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to load the employer hiring workspace",
      ),
    );
  }, []);

  async function decide(proposal: Proposal, decision: "ACCEPTED" | "REJECTED") {
    const decisionReason = decisionReasons[proposal.id]?.trim() ?? "";
    if (decisionReason.length < 20) {
      setError("Add a decision reason of at least 20 characters.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await praxisFetch<Proposal>(
        apiBase,
        `/talent/proposals/${proposal.id}/decision`,
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({ decision, reason: decisionReason }),
        },
      );
      setOpportunities(
        (current) =>
          current?.map((opportunity) => ({
            ...opportunity,
            status:
              decision === "ACCEPTED" &&
              opportunity.id === updated.opportunity_id
                ? "SELECTED"
                : opportunity.status,
            proposals: opportunity.proposals.map((item) =>
              item.id === updated.id
                ? updated
                : decision === "ACCEPTED" &&
                    opportunity.id === updated.opportunity_id &&
                    item.state === "SUBMITTED"
                  ? {
                      ...item,
                      state: "REJECTED",
                      decision_reason:
                        "Another proposal was selected for this opportunity.",
                    }
                  : item,
            ),
          })) ?? [],
      );
      setDecisionReasons((current) => ({ ...current, [proposal.id]: "" }));
      setNotice(
        decision === "ACCEPTED"
          ? "Proposal selected. The student was notified that contracting, scope, and funding must finish before work begins."
          : "Proposal declined with an auditable reason and no reputation penalty.",
      );
    } catch (caught: unknown) {
      if (isDemoPreview) {
        setOpportunities(
          (current) =>
            current?.map((opportunity) =>
              opportunity.id === proposal.opportunity_id
                ? {
                    ...opportunity,
                    status:
                      decision === "ACCEPTED" ? "SELECTED" : opportunity.status,
                    proposals: opportunity.proposals.map((item) =>
                      item.id === proposal.id
                        ? {
                            ...item,
                            state: decision,
                            decision_reason: decisionReason,
                            decided_at: new Date().toISOString(),
                          }
                        : item,
                    ),
                  }
                : opportunity,
            ) ?? [],
        );
        setDecisionReasons((current) => ({ ...current, [proposal.id]: "" }));
        setNotice("Demo decision saved locally. No API record was changed.");
        return;
      }
      setError(
        caught instanceof Error ? caught.message : "Proposal decision failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const lines = (name: string) =>
      String(form.get(name))
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);
    setIsSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const created = await praxisFetch<EmployerOpportunity>(
        apiBase,
        "/talent/employers/me/opportunities",
        {
          method: "POST",
          body: JSON.stringify({
            project_id: String(form.get("projectId")),
            headline: String(form.get("headline")),
            brief: String(form.get("brief")),
            required_skills: lines("requiredSkills"),
            nice_to_have_skills: lines("niceSkills"),
            deliverables: lines("deliverables"),
            proposal_requirements: lines("proposalRequirements"),
            estimated_hours_low: Number(form.get("hoursLow")),
            estimated_hours_high: Number(form.get("hoursHigh")),
            budget_minor: Math.round(Number(form.get("budget")) * 100),
            currency: "USD",
            deadline: new Date(String(form.get("deadline"))).toISOString(),
            supervision_level: String(form.get("supervision")),
            max_proposals: Number(form.get("maxProposals")),
          }),
        },
      );
      setOpportunities((current) => [created, ...(current ?? [])]);
      formElement.reset();
      setNotice(
        "Paid project opportunity published. Students can now review complete terms and submit evidence-backed proposals.",
      );
    } catch (reason: unknown) {
      if (isDemoPreview) {
        const localOpportunity: EmployerOpportunity = {
          id: `demo-opportunity-${Date.now()}`,
          project_id: String(form.get("projectId")),
          headline: String(form.get("headline")),
          brief: String(form.get("brief")),
          required_skills: lines("requiredSkills"),
          nice_to_have_skills: lines("niceSkills"),
          deliverables: lines("deliverables"),
          proposal_requirements: lines("proposalRequirements"),
          estimated_hours_low: Number(form.get("hoursLow")),
          estimated_hours_high: Number(form.get("hoursHigh")),
          budget_minor: Math.round(Number(form.get("budget")) * 100),
          currency: "USD",
          deadline: new Date(String(form.get("deadline"))).toISOString(),
          supervision_level: String(form.get("supervision")),
          employer_name: "Northstar Civic Studio",
          proposal_count: 0,
          proposals: [],
          my_proposal: null,
          created_at: new Date().toISOString(),
          status: "OPEN",
        };
        setOpportunities((current) => [localOpportunity, ...(current ?? [])]);
        formElement.reset();
        setNotice("Demo opportunity saved locally. No API record was changed.");
        return;
      }
      setError(
        reason instanceof Error
          ? reason.message
          : "Opportunity publishing failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (opportunities === null || projects === null) {
    return (
      <div className="career-loading">Loading the employer hiring desk…</div>
    );
  }

  const allProposals = opportunities.flatMap((item) => item.proposals);
  const openOpportunities = opportunities.filter(
    (item) => item.status === "OPEN",
  );
  const pendingProposals = allProposals.filter(
    (item) => item.state === "SUBMITTED",
  );

  return (
    <div className="career-workspace employer-workspace">
      {isDemoPreview && (
        <div className="demo-preview-banner" role="status">
          <span className="demo-pulse" aria-hidden="true" />
          Demo preview · fictional hiring data · local decisions are not
          persisted
        </div>
      )}
      {error && <div className="error career-message">{error}</div>}
      {notice && <div className="notice career-message">{notice}</div>}

      {page === "home" && (
        <>
          <section className="career-hero employer-career-hero">
            <div>
              <span className="career-kicker">Northstar talent desk</span>
              <h2>Hire emerging talent through evidence, not guesswork.</h2>
              <p>
                Publish a bounded paid project, review student approaches and
                work evidence, then select a proposal without bypassing scope,
                supervision, contracting, or funding controls.
              </p>
              <div className="career-actions">
                <Link
                  className="button button-accent"
                  href="/client/opportunities/new"
                >
                  Publish paid project <ArrowRight size={16} />
                </Link>
                <Link
                  className="button career-outline-button"
                  href="/client/proposals"
                >
                  Review proposals
                </Link>
              </div>
            </div>
            <div className="employer-trust-card">
              <ShieldCheck />
              <strong>Supervised delivery model</strong>
              <span>Verified identity</span>
              <span>Visible commercial terms</span>
              <span>Human-reviewed releases</span>
              <span>Audited decisions</span>
            </div>
          </section>
          <section className="career-stat-grid">
            <article>
              <BriefcaseBusiness />
              <strong>{openOpportunities.length}</strong>
              <span>Projects recruiting</span>
            </article>
            <article>
              <Users />
              <strong>{pendingProposals.length}</strong>
              <span>Proposals to review</span>
            </article>
            <article>
              <CheckCircle2 />
              <strong>
                {
                  allProposals.filter((item) => item.state === "ACCEPTED")
                    .length
                }
              </strong>
              <span>Students selected</span>
            </article>
            <article>
              <Clock3 />
              <strong>48h</strong>
              <span>Target response time</span>
            </article>
          </section>
          <div className="career-two-column">
            <section className="career-surface">
              <div className="career-section-head">
                <div>
                  <span className="career-kicker dark">Hiring pipeline</span>
                  <h3>Projects and response</h3>
                </div>
                <Link href="/client/proposals">Open hiring desk</Link>
              </div>
              {opportunities.map((item) => (
                <article className="hiring-pipeline-row" key={item.id}>
                  <span
                    className={`opportunity-status ${item.status.toLowerCase()}`}
                  >
                    {item.status}
                  </span>
                  <div>
                    <strong>{item.headline}</strong>
                    <small>
                      {item.proposal_count} proposals ·{" "}
                      {item.estimated_hours_low}–{item.estimated_hours_high}{" "}
                      hours
                    </small>
                  </div>
                  <MoneyAmount
                    amountMinor={item.budget_minor}
                    currency={item.currency}
                  />
                </article>
              ))}
            </section>
            <section className="career-surface">
              <div className="career-section-head">
                <div>
                  <span className="career-kicker dark">What you evaluate</span>
                  <h3>A complete proposal record</h3>
                </div>
              </div>
              <div className="evaluation-list">
                <span>
                  <Sparkles />
                  Fit to the business outcome and required skills
                </span>
                <span>
                  <FileSearch />
                  Relevant evidence with an explanation of its value
                </span>
                <span>
                  <Clock3 />
                  Milestone plan, delivery days, and weekly availability
                </span>
                <span>
                  <Building2 />
                  Fixed proposal amount within the published budget
                </span>
              </div>
            </section>
          </div>
        </>
      )}

      {page === "proposals" && (
        <>
          <section className="workspace-intro">
            <div>
              <span className="career-kicker dark">Employer hiring desk</span>
              <h2>Compare the evidence behind every proposal.</h2>
              <p>
                Review approach, milestones, work samples, price, availability,
                and timing. Every accept or reject decision is recorded with
                your reason.
              </p>
            </div>
            <div className="information-callout">
              <ShieldCheck />
              <span>
                <strong>Selection is not work authorization</strong>An accepted
                proposal enters scope, contract, supervision, and funding
                review.
              </span>
            </div>
          </section>
          <div className="workspace-toolbar">
            <label className="search-field">
              <FileSearch size={16} aria-hidden="true" />
              <span className="sr-only">Search proposals</span>
              <input
                onChange={(event) => setProposalQuery(event.target.value)}
                placeholder="Search proposals, students, or project names"
                value={proposalQuery}
              />
            </label>
            <span className="toolbar-result-count">
              {
                allProposals.filter((proposal) =>
                  `${proposal.student_display_name} ${proposal.approach} ${proposal.cover_note}`
                    .toLowerCase()
                    .includes(proposalQuery.toLowerCase()),
                ).length
              }{" "}
              results
            </span>
          </div>
          <div className="employer-opportunity-list">
            {opportunities.map((opportunity) => (
              <article
                className="employer-opportunity-card"
                key={opportunity.id}
              >
                <header>
                  <div>
                    <span className="company-label">
                      Paid project opportunity
                    </span>
                    <h3>{opportunity.headline}</h3>
                    <p>{opportunity.brief}</p>
                  </div>
                  <div className="employer-budget">
                    <MoneyAmount
                      amountMinor={opportunity.budget_minor}
                      currency={opportunity.currency}
                    />
                    <small>Published budget</small>
                  </div>
                </header>
                <div className="opportunity-facts compact-facts">
                  <span>
                    <strong>
                      {opportunity.estimated_hours_low}–
                      {opportunity.estimated_hours_high}h
                    </strong>
                    Expected effort
                  </span>
                  <span>
                    <strong>
                      {new Date(opportunity.deadline).toLocaleDateString()}
                    </strong>
                    Deadline
                  </span>
                  <span>
                    <strong>{opportunity.supervision_level}</strong>Supervision
                  </span>
                  <span>
                    <strong>{opportunity.proposals.length}</strong>Proposals
                  </span>
                </div>
                <div className="proposal-comparison-list">
                  {opportunity.proposals.length === 0 ? (
                    <div className="empty">No student proposals yet.</div>
                  ) : (
                    opportunity.proposals
                      .filter((proposal) =>
                        `${proposal.student_display_name} ${proposal.approach} ${proposal.cover_note}`
                          .toLowerCase()
                          .includes(proposalQuery.toLowerCase()),
                      )
                      .map((proposal) => (
                        <article
                          className="employer-proposal-card"
                          key={proposal.id}
                        >
                          <header>
                            <div className="student-avatar">
                              {proposal.student_display_name
                                .split(" ")
                                .map((part) => part[0])
                                .join("")
                                .slice(0, 2)}
                            </div>
                            <div>
                              <h4>{proposal.student_display_name}</h4>
                              <span>
                                Submitted{" "}
                                {new Date(
                                  proposal.created_at,
                                ).toLocaleDateString()}
                              </span>
                            </div>
                            <span
                              className={`proposal-state ${proposal.state.toLowerCase()}`}
                            >
                              {proposal.state}
                            </span>
                          </header>
                          <div className="proposal-facts">
                            <span>
                              <strong>
                                <MoneyAmount
                                  amountMinor={proposal.proposed_amount_minor}
                                  currency={proposal.currency}
                                />
                              </strong>
                              Fixed amount
                            </span>
                            <span>
                              <strong>{proposal.estimated_days} days</strong>
                              Delivery
                            </span>
                            <span>
                              <strong>
                                {proposal.availability_hours_per_week}h/week
                              </strong>
                              Availability
                            </span>
                          </div>
                          <div className="proposal-review-grid">
                            <section>
                              <h5>Why this student</h5>
                              <p>{proposal.cover_note}</p>
                              <h5>Delivery approach</h5>
                              <p>{proposal.approach}</p>
                            </section>
                            <section>
                              <h5>Milestone plan</h5>
                              <ol>
                                {proposal.delivery_plan.map((step) => (
                                  <li key={step.milestone}>
                                    <strong>{step.milestone}</strong>
                                    <span>{step.outcome}</span>
                                  </li>
                                ))}
                              </ol>
                              <h5>Relevant evidence</h5>
                              {proposal.relevant_evidence.map((evidence) => (
                                <a
                                  className="evidence-link"
                                  href={evidence.url}
                                  key={evidence.title}
                                  rel="noreferrer"
                                  target="_blank"
                                >
                                  <FileSearch size={16} />
                                  <span>
                                    <strong>{evidence.title}</strong>
                                    {evidence.relevance}
                                  </span>
                                </a>
                              ))}
                            </section>
                          </div>
                          {proposal.state === "SUBMITTED" ? (
                            <div className="decision-controls">
                              <label>
                                Decision reason
                                <textarea
                                  minLength={20}
                                  onChange={(event) =>
                                    setDecisionReasons((current) => ({
                                      ...current,
                                      [proposal.id]: event.target.value,
                                    }))
                                  }
                                  placeholder="Explain the evidence behind your decision."
                                  rows={3}
                                  value={decisionReasons[proposal.id] ?? ""}
                                />
                              </label>
                              <div>
                                <button
                                  className="button accept-button"
                                  disabled={isSubmitting}
                                  onClick={() =>
                                    void decide(proposal, "ACCEPTED")
                                  }
                                  type="button"
                                >
                                  Accept proposal
                                </button>
                                <button
                                  className="button button-ghost"
                                  disabled={isSubmitting}
                                  onClick={() =>
                                    void decide(proposal, "REJECTED")
                                  }
                                  type="button"
                                >
                                  Reject with reason
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="decision-note">
                              <strong>Recorded employer decision</strong>
                              {proposal.decision_reason}
                            </div>
                          )}
                        </article>
                      ))
                  )}
                </div>
              </article>
            ))}
          </div>
        </>
      )}

      {page === "publish" && (
        <>
          <section className="workspace-intro">
            <div>
              <span className="career-kicker dark">New paid opportunity</span>
              <h2>
                Give students enough information to propose professionally.
              </h2>
              <p>
                Publish the business context, concrete deliverables, required
                skills, budget, timing, supervision, and exactly what a strong
                proposal must contain.
              </p>
            </div>
          </section>
          <form className="publish-opportunity-form" onSubmit={publish}>
            <section>
              <span className="form-section-number">01</span>
              <div>
                <h3>Connect the approved project</h3>
                <p>
                  Opportunities are attached to a client project so later scope,
                  funding, delivery, and credential evidence stay connected.
                </p>
                <label>
                  Client project
                  <select name="projectId" required>
                    <option value="">Select a project</option>
                    {projects
                      .filter(
                        (project) =>
                          !opportunities.some(
                            (item) => item.project_id === project.id,
                          ) &&
                          !["ACTIVE", "COMPLETED", "CANCELED"].includes(
                            project.state,
                          ),
                      )
                      .map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.title} · {project.state.replaceAll("_", " ")}
                        </option>
                      ))}
                  </select>
                </label>
              </div>
            </section>
            <section>
              <span className="form-section-number">02</span>
              <div>
                <h3>Explain the work like a real company</h3>
                <div className="form-grid">
                  <label>
                    Opportunity headline
                    <input minLength={5} name="headline" required />
                  </label>
                  <label>
                    Supervision level
                    <select name="supervision" required>
                      <option value="guided">
                        Guided · regular lead review
                      </option>
                      <option value="supported">
                        Supported · milestone review
                      </option>
                      <option value="independent">
                        Independent · release review
                      </option>
                    </select>
                  </label>
                </div>
                <label>
                  Business context and user outcome
                  <textarea
                    minLength={80}
                    name="brief"
                    placeholder="Who needs this, what problem exists, what outcome matters, and what boundaries are already known?"
                    required
                    rows={6}
                  />
                </label>
              </div>
            </section>
            <section>
              <span className="form-section-number">03</span>
              <div>
                <h3>Define deliverables and selection evidence</h3>
                <div className="form-grid">
                  <label>
                    Deliverables <small>One per line</small>
                    <textarea
                      minLength={5}
                      name="deliverables"
                      required
                      rows={6}
                    />
                  </label>
                  <label>
                    Proposal requirements <small>One per line</small>
                    <textarea
                      minLength={5}
                      name="proposalRequirements"
                      required
                      rows={6}
                    />
                  </label>
                  <label>
                    Required skills <small>One per line</small>
                    <textarea
                      minLength={2}
                      name="requiredSkills"
                      required
                      rows={5}
                    />
                  </label>
                  <label>
                    Nice-to-have skills <small>One per line</small>
                    <textarea name="niceSkills" rows={5} />
                  </label>
                </div>
              </div>
            </section>
            <section>
              <span className="form-section-number">04</span>
              <div>
                <h3>Publish transparent commercial terms</h3>
                <div className="proposal-form-grid">
                  <label>
                    Low effort hours
                    <input min="1" name="hoursLow" required type="number" />
                  </label>
                  <label>
                    High effort hours
                    <input min="1" name="hoursHigh" required type="number" />
                  </label>
                  <label>
                    Maximum budget (USD)
                    <input
                      min="0.01"
                      name="budget"
                      required
                      step="0.01"
                      type="number"
                    />
                  </label>
                  <label>
                    Target deadline
                    <input name="deadline" required type="datetime-local" />
                  </label>
                  <label>
                    Maximum proposals
                    <input
                      defaultValue="20"
                      max="100"
                      min="1"
                      name="maxProposals"
                      required
                      type="number"
                    />
                  </label>
                </div>
                <div className="proposal-protection">
                  <ShieldCheck />
                  <span>
                    <strong>Publishing does not authorize work.</strong> A
                    selected proposal still requires final scope, contract,
                    supervision, and verified funding.
                  </span>
                </div>
                <button
                  className="button button-primary"
                  disabled={isSubmitting}
                  type="submit"
                >
                  Publish paid opportunity
                </button>
              </div>
            </section>
          </form>
        </>
      )}
    </div>
  );
}
