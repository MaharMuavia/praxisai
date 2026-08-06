"use client";

import { praxisFetch, type components } from "@praxisai/api-client";
import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Code2,
  FileText,
  GraduationCap,
  Search,
  ShieldCheck,
  Target,
} from "lucide-react";
import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { demoWorkspaceSnapshot, withDemoFallback } from "../lib/demo-data";
import { MoneyAmount } from "./money-amount";
import { apiBase } from "../lib/api";

type LearningPath = components["schemas"]["LearningPathView"];
type Opportunity = components["schemas"]["OpportunityView"];
type Proposal = components["schemas"]["StudentProposalView"];

type PageKind = "home" | "learn" | "opportunities" | "proposals";

function proposalStateLabel(state: string) {
  if (state === "ACCEPTED") return "Selected by employer";
  if (state === "REJECTED") return "Not selected";
  return "Employer review";
}

export function StudentCareerWorkspace({ page }: { page: PageKind }) {
  const [paths, setPaths] = useState<LearningPath[] | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[] | null>(
    null,
  );
  const [proposals, setProposals] = useState<Proposal[] | null>(null);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<
    string | null
  >(null);
  const [completionModuleId, setCompletionModuleId] = useState<string | null>(
    null,
  );
  const [completionEvidence, setCompletionEvidence] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoPreview, setIsDemoPreview] = useState(false);
  const [opportunityQuery, setOpportunityQuery] = useState("");
  const [opportunityFilter, setOpportunityFilter] = useState("all");
  const [expandedOpportunityId, setExpandedOpportunityId] = useState<
    string | null
  >(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const result = await withDemoFallback(
          Promise.all([
            praxisFetch<LearningPath[]>(apiBase, "/learning/paths"),
            praxisFetch<Opportunity[]>(apiBase, "/talent/opportunities"),
            praxisFetch<Proposal[]>(apiBase, "/talent/students/me/proposals"),
          ]),
          [
            demoWorkspaceSnapshot.learningPaths,
            demoWorkspaceSnapshot.opportunities,
            demoWorkspaceSnapshot.proposals,
          ] as [LearningPath[], Opportunity[], Proposal[]],
        );
        if (cancelled) return;
        const [nextPaths, nextOpportunities, nextProposals] = result.data;
        setPaths(nextPaths);
        setOpportunities(nextOpportunities);
        setProposals(nextProposals);
        setIsDemoPreview(result.isDemo);
      } catch (reason: unknown) {
        if (cancelled) return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to load the student career workspace",
        );
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedOpportunity = opportunities?.find(
    (item) => item.id === selectedOpportunityId,
  );
  const activePath = paths?.find(
    (path) => path.enrolled && path.status !== "COMPLETED",
  );
  const completedModules =
    paths?.flatMap((path) => path.modules).filter((module) => module.completed)
      .length ?? 0;
  const totalModules = paths?.flatMap((path) => path.modules).length ?? 0;
  const readiness = totalModules
    ? Math.round(
        (completedModules / totalModules) * 60 +
          Math.min(40, (proposals?.length ?? 0) * 10),
      )
    : 0;
  const filteredOpportunities =
    opportunities?.filter((item) => {
      const haystack =
        `${item.headline} ${item.employer_name} ${item.brief} ${item.required_skills.join(" ")}`.toLowerCase();
      const matchesQuery = haystack.includes(opportunityQuery.toLowerCase());
      const matchesFilter =
        opportunityFilter === "all" ||
        (opportunityFilter === "applied" && item.my_proposal !== null) ||
        (opportunityFilter === "open" && item.status === "OPEN");
      return matchesQuery && matchesFilter;
    }) ?? [];
  async function enroll(pathId: string) {
    setIsSubmitting(true);
    setError(null);
    try {
      const updated = await praxisFetch<LearningPath>(
        apiBase,
        `/learning/paths/${pathId}/enroll`,
        { method: "POST" },
      );
      setPaths(
        (current) =>
          current?.map((item) => (item.id === updated.id ? updated : item)) ??
          [],
      );
      setNotice(
        "Learning path started. Complete the modules in order and keep evidence of your practice.",
      );
    } catch (reason: unknown) {
      if (isDemoPreview) {
        setPaths(
          (current) =>
            current?.map((item) =>
              item.id === pathId
                ? { ...item, enrolled: true, status: "IN_PROGRESS" }
                : item,
            ) ?? [],
        );
        setNotice(
          "Demo update saved locally. The learning path is now active.",
        );
        return;
      }
      setError(reason instanceof Error ? reason.message : "Enrollment failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function completeModule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!completionModuleId) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const updated = await praxisFetch<LearningPath>(
        apiBase,
        `/learning/modules/${completionModuleId}/complete`,
        {
          method: "POST",
          body: JSON.stringify({ evidence_summary: completionEvidence }),
        },
      );
      setPaths(
        (current) =>
          current?.map((item) => (item.id === updated.id ? updated : item)) ??
          [],
      );
      setCompletionModuleId(null);
      setCompletionEvidence("");
      setNotice(
        "Practice evidence recorded. This is learning progress, not an employer-verified credential.",
      );
    } catch (reason: unknown) {
      if (isDemoPreview) {
        setPaths(
          (current) =>
            current?.map((path) =>
              path.modules.some((module) => module.id === completionModuleId)
                ? {
                    ...path,
                    progress_percent: Math.min(100, path.progress_percent + 14),
                    modules: path.modules.map((module) =>
                      module.id === completionModuleId
                        ? {
                            ...module,
                            completed: true,
                            completion_evidence: completionEvidence,
                          }
                        : module,
                    ),
                  }
                : path,
            ) ?? [],
        );
        setCompletionModuleId(null);
        setCompletionEvidence("");
        setNotice("Demo evidence recorded locally. No API record was changed.");
        return;
      }
      setError(
        reason instanceof Error ? reason.message : "Module completion failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitProposal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOpportunity) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const plan = String(form.get("deliveryPlan"))
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [milestone, ...outcome] = line.split("|");
        return {
          milestone: milestone.trim(),
          outcome: outcome.join("|").trim(),
        };
      });
    setIsSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const created = await praxisFetch<Proposal>(
        apiBase,
        `/talent/opportunities/${selectedOpportunity.id}/proposals`,
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({
            cover_note: String(form.get("coverNote")),
            approach: String(form.get("approach")),
            delivery_plan: plan,
            relevant_evidence: [
              {
                title: String(form.get("evidenceTitle")),
                url: String(form.get("evidenceUrl")),
                relevance: String(form.get("evidenceRelevance")),
              },
            ],
            proposed_amount_minor: Math.round(Number(form.get("amount")) * 100),
            currency: selectedOpportunity.currency,
            estimated_days: Number(form.get("estimatedDays")),
            availability_hours_per_week: Number(form.get("weeklyHours")),
          }),
        },
      );
      setProposals((current) => [created, ...(current ?? [])]);
      setOpportunities(
        (current) =>
          current?.map((item) =>
            item.id === created.opportunity_id
              ? {
                  ...item,
                  my_proposal: created,
                  proposal_count: item.proposal_count + 1,
                }
              : item,
          ) ?? [],
      );
      formElement.reset();
      setSelectedOpportunityId(null);
      setNotice(
        "Proposal submitted with immutable terms. The employer can accept or reject it; no work begins before contracting and funding review.",
      );
    } catch (reason: unknown) {
      if (isDemoPreview) {
        const demoProposal: Proposal = {
          id: `demo-proposal-${Date.now()}`,
          opportunity_id: selectedOpportunity.id,
          student_user_id: "demo-student",
          student_display_name: "Amina Noor",
          state: "SUBMITTED",
          cover_note: String(form.get("coverNote")),
          approach: String(form.get("approach")),
          delivery_plan: plan,
          relevant_evidence: [
            {
              title: String(form.get("evidenceTitle")),
              url: String(form.get("evidenceUrl")),
              relevance: String(form.get("evidenceRelevance")),
            },
          ],
          proposed_amount_minor: Math.round(Number(form.get("amount")) * 100),
          currency: selectedOpportunity.currency,
          estimated_days: Number(form.get("estimatedDays")),
          availability_hours_per_week: Number(form.get("weeklyHours")),
          created_at: new Date().toISOString(),
          decided_at: null,
          decision_reason: null,
        };
        setProposals((current) => [demoProposal, ...(current ?? [])]);
        setOpportunities(
          (current) =>
            current?.map((item) =>
              item.id === selectedOpportunity.id
                ? {
                    ...item,
                    my_proposal: demoProposal,
                    proposal_count: item.proposal_count + 1,
                  }
                : item,
            ) ?? [],
        );
        formElement.reset();
        setSelectedOpportunityId(null);
        setNotice("Demo proposal saved locally. No API record was changed.");
        return;
      }
      setError(
        reason instanceof Error ? reason.message : "Proposal submission failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (paths === null || opportunities === null || proposals === null) {
    return <div className="career-loading">Loading your career workspace…</div>;
  }

  return (
    <div className="career-workspace">
      {isDemoPreview && (
        <div className="demo-preview-banner" role="status">
          <span className="demo-pulse" aria-hidden="true" />
          Demo preview · fictional data · local interactions are not persisted
        </div>
      )}
      {error && <div className="error career-message">{error}</div>}
      {notice && <div className="notice career-message">{notice}</div>}

      {page === "home" && (
        <>
          <section className="career-hero student-career-hero">
            <div>
              <span className="career-kicker">Your professional launchpad</span>
              <h2>Learn the work. Prove the skill. Win the project.</h2>
              <p>
                Build employer-relevant skills through structured practice, then
                use concrete evidence to propose on paid, supervised projects.
              </p>
              <div className="career-actions">
                <Link className="button button-accent" href="/student/learn">
                  Continue learning <ArrowRight size={16} />
                </Link>
                <Link
                  className="button career-outline-button"
                  href="/student/opportunities"
                >
                  Browse paid projects
                </Link>
              </div>
            </div>
            <div className="readiness-card">
              <span>Career readiness</span>
              <strong>{readiness}%</strong>
              <div className="progress-track">
                <span style={{ width: `${readiness}%` }} />
              </div>
              <small>Learning progress plus real proposal practice</small>
            </div>
          </section>

          <section className="career-stat-grid">
            <article>
              <GraduationCap />
              <strong>{completedModules}</strong>
              <span>Modules completed</span>
            </article>
            <article>
              <BriefcaseBusiness />
              <strong>
                {opportunities.filter((item) => item.status === "OPEN").length}
              </strong>
              <span>Paid projects open</span>
            </article>
            <article>
              <FileText />
              <strong>{proposals.length}</strong>
              <span>Proposals submitted</span>
            </article>
            <article>
              <ShieldCheck />
              <strong>
                {proposals.filter((item) => item.state === "ACCEPTED").length}
              </strong>
              <span>Employer selections</span>
            </article>
          </section>

          <section
            className="insight-strip"
            aria-label="Student progress signals"
          >
            <div>
              <span className="insight-label">Weekly momentum</span>
              <strong>+18%</strong>
              <small>practice activity over the last 6 weeks</small>
            </div>
            <div className="mini-bars" aria-label="Practice activity trend">
              {[34, 42, 48, 51, 66, 78, 72].map((height, index) => (
                <span key={index} style={{ height: `${height}%` }} />
              ))}
            </div>
            <div className="insight-next">
              <span className="insight-label">Next best action</span>
              <strong>Finish “Prove the release”</strong>
              <Link href="/student/learn">
                Open module <ArrowRight size={14} />
              </Link>
            </div>
          </section>

          <div className="career-two-column">
            <section className="career-surface">
              <div className="career-section-head">
                <div>
                  <span className="career-kicker dark">
                    Current learning path
                  </span>
                  <h3>{activePath?.title ?? "Choose your first path"}</h3>
                </div>
                <Link href="/student/learn">View curriculum</Link>
              </div>
              {activePath ? (
                <>
                  <p>{activePath.summary}</p>
                  <div className="progress-label">
                    <span>{activePath.progress_percent}% complete</span>
                    <span>{activePath.estimated_hours} hours</span>
                  </div>
                  <div className="progress-track light">
                    <span
                      style={{ width: `${activePath.progress_percent}%` }}
                    />
                  </div>
                  <div className="next-module">
                    <BookOpen />
                    <span>
                      <small>Next module</small>
                      <strong>
                        {activePath.modules.find((module) => !module.completed)
                          ?.title ?? "Path complete"}
                      </strong>
                    </span>
                  </div>
                </>
              ) : (
                <p>
                  Select a curriculum designed around the evidence employers ask
                  for.
                </p>
              )}
            </section>
            <section className="career-surface">
              <div className="career-section-head">
                <div>
                  <span className="career-kicker dark">Recommended work</span>
                  <h3>Projects matched to practice</h3>
                </div>
                <Link href="/student/opportunities">See all</Link>
              </div>
              {opportunities
                .filter((item) => item.status === "OPEN" && !item.my_proposal)
                .slice(0, 2)
                .map((item) => (
                  <article className="compact-opportunity" key={item.id}>
                    <div>
                      <strong>{item.headline}</strong>
                      <small>{item.employer_name}</small>
                    </div>
                    <MoneyAmount
                      amountMinor={item.budget_minor}
                      currency={item.currency}
                    />
                    <div className="skill-tags">
                      {item.required_skills.slice(0, 3).map((skill) => (
                        <span key={skill}>{skill}</span>
                      ))}
                    </div>
                  </article>
                ))}
            </section>
          </div>
        </>
      )}

      {page === "learn" && (
        <>
          <section className="workspace-intro">
            <div>
              <span className="career-kicker dark">PraxisAI Academy</span>
              <h2>Learn skills employers can evaluate.</h2>
              <p>
                Every module ends with applied practice and an evidence
                requirement. Learning completion is separate from
                employer-verified project credentials.
              </p>
            </div>
            <div className="information-callout">
              <Target />
              <span>
                <strong>How this helps</strong>Use module evidence in proposals,
                then earn stronger verification through accepted project work.
              </span>
            </div>
          </section>
          <div className="learning-path-list">
            {paths.map((path) => (
              <article className="learning-path-card" key={path.id}>
                <header>
                  <div>
                    <span className="level-pill">{path.level}</span>
                    <h3>{path.title}</h3>
                    <p>{path.summary}</p>
                  </div>
                  <div className="path-progress">
                    <strong>{path.progress_percent}%</strong>
                    <span>{path.estimated_hours}h curriculum</span>
                  </div>
                </header>
                <div className="path-meta-grid">
                  <div>
                    <small>Skills you will build</small>
                    <ul>
                      {path.skill_outcomes.map((skill) => (
                        <li key={skill}>
                          <CheckCircle2 size={14} />
                          {skill}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <small>Prerequisites</small>
                    <ul>
                      {path.prerequisites.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                {!path.enrolled ? (
                  <button
                    className="button button-primary"
                    disabled={isSubmitting}
                    onClick={() => void enroll(path.id)}
                    type="button"
                  >
                    Start this learning path
                  </button>
                ) : (
                  <div className="module-list">
                    {path.modules.map((module, index) => {
                      const locked =
                        index > 0 && !path.modules[index - 1].completed;
                      return (
                        <details className="module-card" key={module.id}>
                          <summary>
                            <span
                              className={
                                module.completed
                                  ? "module-number complete"
                                  : "module-number"
                              }
                            >
                              {module.completed ? (
                                <CheckCircle2 size={17} />
                              ) : (
                                module.ordinal
                              )}
                            </span>
                            <span>
                              <strong>{module.title}</strong>
                              <small>{module.summary}</small>
                            </span>
                            <span className="module-time">
                              <Clock3 size={14} /> {module.estimated_minutes}{" "}
                              min
                            </span>
                          </summary>
                          <div className="module-content">
                            {module.content_sections.map((section) => (
                              <section key={section.title}>
                                <h4>{section.title}</h4>
                                <p>{section.body}</p>
                              </section>
                            ))}
                            <div className="practice-brief">
                              <Code2 />
                              <span>
                                <strong>Applied exercise</strong>
                                {module.exercise_brief}
                                <small>
                                  Evidence expected:{" "}
                                  {module.completion_evidence}
                                </small>
                              </span>
                            </div>
                            {!module.completed &&
                              (completionModuleId === module.id ? (
                                <form
                                  className="evidence-form"
                                  onSubmit={completeModule}
                                >
                                  <label>
                                    Describe the evidence you produced
                                    <textarea
                                      minLength={20}
                                      onChange={(event) =>
                                        setCompletionEvidence(
                                          event.target.value,
                                        )
                                      }
                                      required
                                      rows={4}
                                      value={completionEvidence}
                                    />
                                  </label>
                                  <div>
                                    <button
                                      className="button button-primary"
                                      disabled={isSubmitting}
                                      type="submit"
                                    >
                                      Record practice evidence
                                    </button>
                                    <button
                                      className="button button-ghost"
                                      onClick={() =>
                                        setCompletionModuleId(null)
                                      }
                                      type="button"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </form>
                              ) : (
                                <button
                                  className="button button-primary"
                                  disabled={locked}
                                  onClick={() =>
                                    setCompletionModuleId(module.id)
                                  }
                                  type="button"
                                >
                                  {locked
                                    ? "Complete previous module first"
                                    : "Submit module evidence"}
                                </button>
                              ))}
                          </div>
                        </details>
                      );
                    })}
                  </div>
                )}
              </article>
            ))}
          </div>
        </>
      )}

      {page === "opportunities" && (
        <>
          <section className="workspace-intro">
            <div>
              <span className="career-kicker dark">
                Paid project marketplace
              </span>
              <h2>Choose work that builds your career.</h2>
              <p>
                Budgets, expected hours, deliverables, review support, and
                proposal requirements are visible before you apply.
              </p>
            </div>
            <div className="information-callout">
              <ShieldCheck />
              <span>
                <strong>Protected participation</strong>Submitting, withdrawing,
                rejection, or expiry never lowers your reputation.
              </span>
            </div>
          </section>
          <div className="workspace-toolbar">
            <label className="search-field">
              <Search size={16} aria-hidden="true" />
              <span className="sr-only">Search opportunities</span>
              <input
                onChange={(event) => setOpportunityQuery(event.target.value)}
                placeholder="Search by role, skill, or employer"
                value={opportunityQuery}
              />
            </label>
            <div
              className="segmented-control"
              role="group"
              aria-label="Opportunity filters"
            >
              {[
                ["all", "All projects"],
                ["open", "Open now"],
                ["applied", "Applied"],
              ].map(([value, label]) => (
                <button
                  aria-pressed={opportunityFilter === value}
                  className={opportunityFilter === value ? "selected" : ""}
                  key={value}
                  onClick={() => setOpportunityFilter(value)}
                  type="button"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="opportunity-list">
            {filteredOpportunities.map((item) => (
              <article className="opportunity-card" key={item.id}>
                <header>
                  <div>
                    <span className="company-label">{item.employer_name}</span>
                    <h3>{item.headline}</h3>
                  </div>
                  <span
                    className={`opportunity-status ${item.status.toLowerCase()}`}
                  >
                    {item.status}
                  </span>
                </header>
                <p className="opportunity-brief">{item.brief}</p>
                <div className="opportunity-facts">
                  <span>
                    <strong>
                      <MoneyAmount
                        amountMinor={item.budget_minor}
                        currency={item.currency}
                      />
                    </strong>
                    Published budget
                  </span>
                  <span>
                    <strong>
                      {item.estimated_hours_low}–{item.estimated_hours_high}h
                    </strong>
                    Expected effort
                  </span>
                  <span>
                    <strong>
                      {new Date(item.deadline).toLocaleDateString()}
                    </strong>
                    Target deadline
                  </span>
                  <span>
                    <strong>{item.supervision_level}</strong>Review support
                  </span>
                </div>
                <div className="opportunity-detail-grid">
                  <div>
                    <h4>What you will deliver</h4>
                    <ul>
                      {item.deliverables.map((deliverable) => (
                        <li key={deliverable}>{deliverable}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4>Proposal must include</h4>
                    <ul>
                      {item.proposal_requirements.map((requirement) => (
                        <li key={requirement}>{requirement}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="skill-tags large">
                  {item.required_skills.map((skill) => (
                    <span key={skill}>{skill}</span>
                  ))}
                </div>
                <button
                  className="details-toggle"
                  aria-expanded={expandedOpportunityId === item.id}
                  onClick={() =>
                    setExpandedOpportunityId((current) =>
                      current === item.id ? null : item.id,
                    )
                  }
                  type="button"
                >
                  {expandedOpportunityId === item.id
                    ? "Hide project detail"
                    : "View project detail"}
                  <ArrowRight size={15} />
                </button>
                {expandedOpportunityId === item.id && (
                  <div className="expanded-detail">
                    <strong>Why this work matters</strong>
                    <p>
                      This fictional opportunity connects your practice evidence
                      to a real delivery shape: visible scope, a supported
                      review path, and a release that can be explained to a
                      future employer.
                    </p>
                  </div>
                )}
                <footer>
                  <span>
                    {item.proposal_count} proposal
                    {item.proposal_count === 1 ? "" : "s"} submitted
                  </span>
                  {item.my_proposal ? (
                    <span className="proposal-submitted">
                      <CheckCircle2 size={16} />{" "}
                      {proposalStateLabel(item.my_proposal.state)}
                    </span>
                  ) : item.status === "OPEN" ? (
                    <button
                      className="button button-primary"
                      onClick={() => setSelectedOpportunityId(item.id)}
                      type="button"
                    >
                      Build proposal <ArrowRight size={16} />
                    </button>
                  ) : null}
                </footer>
              </article>
            ))}
          </div>
          {filteredOpportunities.length === 0 && (
            <div className="empty filtered-empty">
              No projects match that view. Try another skill, employer, or
              filter.
            </div>
          )}
        </>
      )}

      {page === "proposals" && (
        <>
          <section className="workspace-intro">
            <div>
              <span className="career-kicker dark">My proposals</span>
              <h2>Track every employer decision.</h2>
              <p>
                Your submitted approach and commercial terms stay immutable.
                Employer decisions include a reason and never silently change
                your reputation.
              </p>
            </div>
          </section>
          <div className="proposal-list">
            {proposals.length === 0 ? (
              <div className="empty">
                You have not submitted a proposal yet.
              </div>
            ) : (
              proposals.map((proposal) => {
                const opportunity = opportunities.find(
                  (item) => item.id === proposal.opportunity_id,
                );
                return (
                  <article className="student-proposal-card" key={proposal.id}>
                    <header>
                      <div>
                        <span className="company-label">
                          {opportunity?.employer_name ?? "Employer"}
                        </span>
                        <h3>{opportunity?.headline ?? "Project proposal"}</h3>
                        <small>
                          Submitted{" "}
                          {new Date(proposal.created_at).toLocaleDateString()}
                        </small>
                      </div>
                      <span
                        className={`proposal-state ${proposal.state.toLowerCase()}`}
                      >
                        {proposalStateLabel(proposal.state)}
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
                        Fixed proposal
                      </span>
                      <span>
                        <strong>{proposal.estimated_days} days</strong>Delivery
                        plan
                      </span>
                      <span>
                        <strong>
                          {proposal.availability_hours_per_week}h/week
                        </strong>
                        Availability
                      </span>
                    </div>
                    <p>{proposal.cover_note}</p>
                    {proposal.decision_reason && (
                      <div className="decision-note">
                        <strong>Employer decision note</strong>
                        {proposal.decision_reason}
                      </div>
                    )}
                    {proposal.state === "ACCEPTED" && (
                      <div className="information-callout compact">
                        <ShieldCheck />
                        <span>
                          <strong>Next gate</strong>Contracting, final scope,
                          and funding must be approved before work starts.
                        </span>
                      </div>
                    )}
                  </article>
                );
              })
            )}
          </div>
        </>
      )}

      {selectedOpportunity && (
        <div
          className="proposal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="proposal-title"
        >
          <div className="proposal-builder">
            <header>
              <div>
                <span className="career-kicker dark">Student proposal</span>
                <h2 id="proposal-title">{selectedOpportunity.headline}</h2>
                <p>
                  {selectedOpportunity.employer_name} · budget up to{" "}
                  <MoneyAmount
                    amountMinor={selectedOpportunity.budget_minor}
                    currency={selectedOpportunity.currency}
                  />
                </p>
              </div>
              <button
                aria-label="Close proposal builder"
                className="close-button"
                onClick={() => setSelectedOpportunityId(null)}
                type="button"
              >
                ×
              </button>
            </header>
            <form onSubmit={submitProposal}>
              <label>
                Why you are a strong fit
                <textarea
                  minLength={40}
                  name="coverNote"
                  placeholder="Connect your skills and evidence to this employer's outcome."
                  required
                  rows={4}
                />
              </label>
              <label>
                Your technical and delivery approach
                <textarea
                  minLength={80}
                  name="approach"
                  placeholder="Explain how you will clarify, build, test, communicate, and prepare review evidence."
                  required
                  rows={6}
                />
              </label>
              <label>
                Milestone plan{" "}
                <small>One per line: Milestone | observable outcome</small>
                <textarea
                  minLength={15}
                  name="deliveryPlan"
                  placeholder={
                    "Foundation | Approved structure and component plan\nImplementation | Responsive working workflow\nVerification | Tests and handoff evidence"
                  }
                  required
                  rows={5}
                />
              </label>
              <div className="proposal-form-grid">
                <label>
                  Fixed proposal ({selectedOpportunity.currency})
                  <input
                    max={selectedOpportunity.budget_minor / 100}
                    min="0.01"
                    name="amount"
                    required
                    step="0.01"
                    type="number"
                  />
                </label>
                <label>
                  Estimated calendar days
                  <input
                    max="120"
                    min="1"
                    name="estimatedDays"
                    required
                    type="number"
                  />
                </label>
                <label>
                  Available hours/week
                  <input
                    max="40"
                    min="1"
                    name="weeklyHours"
                    required
                    type="number"
                  />
                </label>
              </div>
              <div className="evidence-block">
                <h3>Relevant evidence</h3>
                <div className="proposal-form-grid">
                  <label>
                    Work sample title
                    <input minLength={3} name="evidenceTitle" required />
                  </label>
                  <label>
                    HTTPS evidence URL
                    <input
                      name="evidenceUrl"
                      pattern="https://.*"
                      required
                      type="url"
                    />
                  </label>
                </div>
                <label>
                  Why this evidence is relevant
                  <textarea
                    minLength={10}
                    name="evidenceRelevance"
                    required
                    rows={3}
                  />
                </label>
              </div>
              <div className="proposal-protection">
                <ShieldCheck />
                <span>
                  <strong>
                    Your proposal is a protected offer to the employer.
                  </strong>{" "}
                  It does not assign you to work. If accepted, final scope,
                  contract, supervision, and verified funding still come first.
                </span>
              </div>
              <div className="proposal-builder-actions">
                <button
                  className="button button-ghost"
                  onClick={() => setSelectedOpportunityId(null)}
                  type="button"
                >
                  Cancel
                </button>
                <button
                  className="button button-primary"
                  disabled={isSubmitting}
                  type="submit"
                >
                  Submit immutable proposal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
