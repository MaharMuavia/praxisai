"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Card, StatusBadge } from "@/components/ui";
import {
  internshipFetch,
  internshipKeys,
  type Dashboard,
} from "@/lib/queries/internships/shared";
import { assignmentsQuery } from "@/lib/queries/internships/assignments";
import { curriculumQuery } from "@/lib/queries/internships/curriculum";
import { dashboardQuery } from "@/lib/queries/internships/dashboard";
import { feedbackQuery } from "@/lib/queries/internships/reviews";
import { applicationQuery } from "@/lib/queries/internships/application";
import { saveInternshipDraft } from "@/lib/queries/internships/submissions";

type PortalView =
  | "dashboard"
  | "application"
  | "learn"
  | "assignments"
  | "feedback"
  | "certificate";

const timelineLabels = [
  "Application",
  "Admission",
  "Week 1",
  "Week 2",
  "Project 1",
  "Project 2",
  "Final review",
  "Certificate",
];

export function InternshipStudentPortal({
  view,
  assignmentId,
}: {
  view: PortalView;
  assignmentId?: string;
}) {
  const queryClient = useQueryClient();
  const dashboard = useQuery(dashboardQuery());
  const application = useQuery({
    ...applicationQuery(),
    enabled: view === "application",
  });
  const curriculum = useQuery({
    ...curriculumQuery(),
    enabled: view === "learn",
  });
  const assignments = useQuery({
    ...assignmentsQuery(),
    enabled: view === "assignments" || Boolean(assignmentId),
  });
  const feedback = useQuery({
    ...feedbackQuery(),
    enabled: view === "feedback",
  });
  const [evidenceUnitId, setEvidenceUnitId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState("");
  const completeUnit = useMutation({
    mutationFn: ({ unitId, summary }: { unitId: string; summary: string }) =>
      internshipFetch(`/internships/me/curriculum/units/${unitId}/complete`, {
        method: "POST",
        body: JSON.stringify({ evidence_summary: summary }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: internshipKeys.curriculum(),
      });
      await queryClient.invalidateQueries({
        queryKey: internshipKeys.dashboard(),
      });
      setEvidenceUnitId(null);
      setEvidence("");
    },
  });

  const error = [
    dashboard,
    application,
    curriculum,
    assignments,
    feedback,
  ].find((query) => query.isError);
  if (error?.error) {
    return (
      <div className="internship-error" role="alert">
        Unable to load this internship workspace.{" "}
        {error.error instanceof Error ? error.error.message : "Try again."}
      </div>
    );
  }

  const assignment = assignmentId
    ? assignments.data?.find((item) => item.id === assignmentId)
    : null;
  return (
    <main className="internship-portal" id="main-content">
      <header className="internship-portal-header">
        <div>
          <span className="marketing-eyebrow">Internship operating system</span>
          <h1>{dashboard.data?.program_name ?? "Technology internship"}</h1>
          <p>
            {dashboard.data?.cohort_name ??
              "Your structured path from learning to reviewed project evidence."}
          </p>
        </div>
        {dashboard.data?.is_demo ? (
          <span className="internship-demo-label">
            Demo data · fictional records
          </span>
        ) : null}
      </header>
      <nav className="internship-local-nav" aria-label="Internship navigation">
        {[
          ["Dashboard", "/student/internship"],
          ["Application", "/student/internship/application"],
          ["Learning", "/student/internship/learn"],
          ["Assignments", "/student/internship/assignments"],
          ["Feedback", "/student/internship/feedback"],
          ["Certificate", "/student/internship/certificate"],
        ].map(([label, href]) => (
          <Link href={href} key={href}>
            {label}
          </Link>
        ))}
      </nav>

      {view === "dashboard" ? (
        <DashboardView dashboard={dashboard.data} />
      ) : null}
      {view === "application" ? (
        <ApplicationView application={application.data} />
      ) : null}
      {view === "learn" ? (
        <section className="internship-section">
          <div className="internship-section-heading">
            <div>
              <span className="marketing-eyebrow">Versioned curriculum</span>
              <h2>{curriculum.data?.track.title ?? "Curriculum"}</h2>
            </div>
            <StatusBadge tone="ai">Server-authoritative</StatusBadge>
          </div>
          {curriculum.data?.weeks.map((week) => (
            <Card className="internship-week" key={week.id}>
              <div className="internship-week-heading">
                <div>
                  <span className="internship-week-number">
                    Week {week.week_number}
                  </span>
                  <h3>{week.title}</h3>
                  <p>{week.summary}</p>
                </div>
                <StatusBadge tone={week.unlocked ? "success" : "warning"}>
                  {week.unlocked ? "Unlocked" : "Locked"}
                </StatusBadge>
              </div>
              <div className="internship-unit-list">
                {week.units.map((unit) => (
                  <article className="internship-unit" key={unit.id}>
                    <div>
                      <span className="internship-unit-type">
                        Learning unit
                      </span>
                      <h4>{unit.title}</h4>
                      <p>{unit.summary}</p>
                      <small>Objectives: {unit.objectives.join(" · ")}</small>
                    </div>
                    <div className="internship-unit-action">
                      <StatusBadge
                        tone={unit.completed ? "success" : "neutral"}
                      >
                        {unit.completed ? "Complete" : "Required"}
                      </StatusBadge>
                      {!unit.completed && week.unlocked ? (
                        <Button
                          onClick={() => setEvidenceUnitId(unit.id)}
                          variant="primary"
                        >
                          Record evidence
                        </Button>
                      ) : null}
                    </div>
                    {evidenceUnitId === unit.id ? (
                      <form
                        className="internship-evidence-form"
                        onSubmit={(event) => {
                          event.preventDefault();
                          completeUnit.mutate({
                            unitId: unit.id,
                            summary: evidence,
                          });
                        }}
                      >
                        <label>
                          Evidence summary
                          <textarea
                            minLength={20}
                            required
                            value={evidence}
                            onChange={(event) =>
                              setEvidence(event.target.value)
                            }
                          />
                        </label>
                        <Button disabled={completeUnit.isPending} type="submit">
                          {completeUnit.isPending
                            ? "Saving…"
                            : "Submit evidence"}
                        </Button>
                      </form>
                    ) : null}
                  </article>
                ))}
              </div>
            </Card>
          ))}
        </section>
      ) : null}
      {view === "assignments" && !assignmentId ? (
        <AssignmentsView assignments={assignments.data ?? []} />
      ) : null}
      {assignmentId ? <AssignmentDetail assignment={assignment} /> : null}
      {view === "feedback" ? (
        <FeedbackView feedback={feedback.data ?? []} />
      ) : null}
      {view === "certificate" ? (
        <CertificateView
          state={dashboard.data?.certificate_eligibility ?? "NOT_ELIGIBLE"}
        />
      ) : null}
    </main>
  );
}

function DashboardView({ dashboard }: { dashboard?: Dashboard }) {
  if (!dashboard)
    return (
      <div className="internship-loading">Loading your internship record…</div>
    );
  return (
    <section className="internship-section">
      <div className="internship-summary-grid">
        <Card>
          <span className="internship-metric-label">Progress</span>
          <strong>{dashboard.progress_percent}%</strong>
          <small>
            {dashboard.completed_units} of {dashboard.required_units} learning
            units · {dashboard.passed_assignments} of{" "}
            {dashboard.required_assignments} assignments
          </small>
        </Card>
        <Card>
          <span className="internship-metric-label">Track</span>
          <strong>{dashboard.track?.name ?? "Pending"}</strong>
          <small>{dashboard.track?.title ?? "Awaiting enrollment"}</small>
        </Card>
        <Card>
          <span className="internship-metric-label">Next gate</span>
          <strong>{dashboard.enrollment_status ?? "Application"}</strong>
          <small>Every transition is determined by the API.</small>
        </Card>
      </div>
      <Card className="internship-timeline-card">
        <div className="internship-section-heading">
          <div>
            <span className="marketing-eyebrow">Program timeline</span>
            <h2>Make the next accountable step visible.</h2>
          </div>
          <span className="internship-demo-label">Evidence-based</span>
        </div>
        <ol className="internship-timeline">
          {timelineLabels.map((label, index) => {
            const item = dashboard.timeline.find((entry) =>
              entry.label
                .toLowerCase()
                .includes(label.toLowerCase().split(" ")[0]),
            );
            const state = item?.state ?? (index < 2 ? "COMPLETE" : "UPCOMING");
            return (
              <li className={state.toLowerCase()} key={label}>
                <span>{index + 1}</span>
                <strong>{label}</strong>
                <small>
                  {state === "COMPLETE"
                    ? "Complete"
                    : state === "CURRENT"
                      ? "Current focus"
                      : "Upcoming"}
                </small>
              </li>
            );
          })}
        </ol>
      </Card>
    </section>
  );
}

function ApplicationView({
  application,
}: {
  application?: {
    status: string;
    version: number;
    motivation: string;
    technical_background: string;
    decision_reason: string | null;
    is_demo: boolean;
  };
}) {
  if (!application)
    return <div className="internship-loading">Loading application…</div>;
  return (
    <section className="internship-section">
      <div className="internship-section-heading">
        <div>
          <span className="marketing-eyebrow">Admissions record</span>
          <h2>Your application is governed by explicit review states.</h2>
        </div>
        <StatusBadge
          tone={application.status === "ACCEPTED" ? "success" : "warning"}
        >
          {application.status.replaceAll("_", " ")}
        </StatusBadge>
      </div>
      <Card className="internship-application-card">
        <dl>
          <div>
            <dt>Application version</dt>
            <dd>{application.version}</dd>
          </div>
          <div>
            <dt>Technical background</dt>
            <dd>{application.technical_background || "Not yet provided"}</dd>
          </div>
          <div>
            <dt>Motivation</dt>
            <dd>{application.motivation || "Not yet provided"}</dd>
          </div>
        </dl>
        {application.decision_reason ? (
          <div className="internship-feedback-note">
            <strong>Decision note</strong>
            <p>{application.decision_reason}</p>
          </div>
        ) : null}
        {application.is_demo ? (
          <p className="internship-demo-note">
            Demo data · this is a fictional application used for product
            walkthroughs.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

function AssignmentsView({
  assignments,
}: {
  assignments: {
    id: string;
    title: string;
    summary: string;
    state: string;
    due_at: string;
    is_late: boolean;
  }[];
}) {
  return (
    <section className="internship-section">
      <div className="internship-section-heading">
        <div>
          <span className="marketing-eyebrow">Practical delivery</span>
          <h2>Assignments with reviewable acceptance criteria.</h2>
        </div>
        <StatusBadge tone="ai">Project work</StatusBadge>
      </div>
      <div className="internship-assignment-list">
        {assignments.map((assignment) => (
          <Card key={assignment.id}>
            <div className="internship-assignment-header">
              <div>
                <span className="internship-unit-type">Assignment</span>
                <h3>{assignment.title}</h3>
                <p>{assignment.summary}</p>
              </div>
              <StatusBadge
                tone={assignment.state === "LOCKED" ? "warning" : "success"}
              >
                {assignment.state.replaceAll("_", " ")}
              </StatusBadge>
            </div>
            <div className="internship-assignment-footer">
              <span>
                Due {new Date(assignment.due_at).toLocaleDateString()}
              </span>
              {assignment.is_late ? (
                <span className="internship-late">Late policy applies</span>
              ) : null}
              <Button
                href={`/student/internship/assignments/${assignment.id}`}
                variant="secondary"
              >
                Open brief
              </Button>
            </div>
          </Card>
        ))}
      </div>
      {assignments.length === 0 ? (
        <div className="internship-empty">
          Assignments appear after admission and release rules are satisfied.
        </div>
      ) : null}
    </section>
  );
}

function AssignmentDetail({
  assignment,
}: {
  assignment?: {
    id: string;
    title: string;
    problem_statement: string;
    objectives: string[];
    deliverables: string[];
    acceptance_criteria: string[];
    required_artifact_types: { type: string; required: boolean }[];
    state: string;
    due_at: string;
  } | null;
}) {
  const router = useRouter();
  const createDraft = useMutation({
    mutationFn: () =>
      saveInternshipDraft(assignment?.id ?? "", {
        links: {},
        text_fields: {},
        artifact_upload_ids: [],
      }),
    onSuccess: (submission) => {
      router.push(`/student/internship/submissions/${submission.id}`);
    },
  });
  if (!assignment)
    return <div className="internship-loading">Loading assignment…</div>;
  return (
    <section className="internship-section">
      <div className="internship-section-heading">
        <div>
          <span className="marketing-eyebrow">Project brief</span>
          <h2>{assignment.title}</h2>
        </div>
        <StatusBadge
          tone={assignment.state === "LOCKED" ? "warning" : "success"}
        >
          {assignment.state.replaceAll("_", " ")}
        </StatusBadge>
      </div>
      <Card className="internship-brief">
        <h3>Problem statement</h3>
        <p>{assignment.problem_statement}</p>
        <div className="internship-brief-grid">
          <div>
            <h3>Objectives</h3>
            <ul>
              {assignment.objectives.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Acceptance criteria</h3>
            <ul>
              {assignment.acceptance_criteria.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
        <h3>Required submission package</h3>
        <ul className="internship-checklist">
          {assignment.required_artifact_types.map((item) => (
            <li key={item.type}>
              <span aria-hidden="true">{item.required ? "□" : "—"}</span>
              {item.type.replaceAll("_", " ")}
            </li>
          ))}
        </ul>
        <p className="internship-deadline">
          Server deadline: {new Date(assignment.due_at).toLocaleString()}
        </p>
        {assignment.state === "LOCKED" ? (
          <div className="internship-locked-message">
            This assignment is locked by cohort release policy. Changing the URL
            does not bypass the server gate.
          </div>
        ) : (
          <Button
            onClick={() => createDraft.mutate()}
            disabled={createDraft.isPending}
            variant="primary"
          >
            {createDraft.isPending
              ? "Opening draft…"
              : "Start a draft submission"}
          </Button>
        )}
        {createDraft.isError ? (
          <p className="form-error" role="alert">
            Unable to open a draft. Check that this assignment is released, then
            try again.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

function FeedbackView({
  feedback,
}: {
  feedback: {
    review_id: string;
    decision: string;
    weighted_total: number;
    student_feedback: string;
    finalized_at: string;
  }[];
}) {
  return (
    <section className="internship-section">
      <div className="internship-section-heading">
        <div>
          <span className="marketing-eyebrow">Review record</span>
          <h2>Feedback that points to the next improvement.</h2>
        </div>
      </div>
      {feedback.map((item) => (
        <Card className="internship-feedback-card" key={item.review_id}>
          <div className="internship-assignment-header">
            <div>
              <h3>{item.decision.replaceAll("_", " ")}</h3>
              <p>
                Finalized {new Date(item.finalized_at).toLocaleDateString()}
              </p>
            </div>
            <strong className="internship-score">
              {item.weighted_total}/100
            </strong>
          </div>
          <p>{item.student_feedback}</p>
        </Card>
      ))}
      {feedback.length === 0 ? (
        <div className="internship-empty">
          No finalized feedback is available yet.
        </div>
      ) : null}
    </section>
  );
}

function CertificateView({ state }: { state: string }) {
  const eligible = state === "ELIGIBLE" || state === "ISSUED";
  return (
    <section className="internship-section">
      <Card className="internship-certificate-card">
        <span className="marketing-eyebrow">Verified completion</span>
        <h2>Certificate eligibility is a human-approved gate.</h2>
        <StatusBadge tone={eligible ? "success" : "warning"}>
          {state.replaceAll("_", " ")}
        </StatusBadge>
        <p>
          {eligible
            ? "All deterministic gates have passed. A coordinator must still issue the certificate."
            : "Complete required learning, pass every assignment, resolve reviews, and obtain coordinator approval before issuance."}
        </p>
      </Card>
    </section>
  );
}
