"use client";

import {
  ArrowUpRight,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  CircleAlert,
  Clock3,
  GraduationCap,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { useState } from "react";
import { demoWorkspaceSnapshot } from "../lib/demo-data";

type WorkspaceRole =
  | "client"
  | "student"
  | "lead"
  | "ops"
  | "admin"
  | "university";

const roleCopy: Record<
  WorkspaceRole,
  { eyebrow: string; title: string; detail: string }
> = {
  client: {
    eyebrow: "Decision cockpit",
    title: "Keep every project moving",
    detail:
      "A sample view of hiring signals, delivery commitments, and the next human decision.",
  },
  student: {
    eyebrow: "Momentum board",
    title: "Turn practice into proof",
    detail:
      "A sample view of readiness, opportunity fit, and the evidence that moves your career forward.",
  },
  lead: {
    eyebrow: "Review desk",
    title: "Make feedback easy to act on",
    detail:
      "A sample view of supervision workload, release confidence, and review decisions.",
  },
  ops: {
    eyebrow: "Control room",
    title: "See the system before it becomes a queue",
    detail: "A sample view of approvals, risks, agent runs, and delivery flow.",
  },
  admin: {
    eyebrow: "Platform pulse",
    title: "Keep the foundation dependable",
    detail:
      "A sample view of integrations, access posture, and operational exceptions.",
  },
  university: {
    eyebrow: "Outcome lens",
    title: "Share outcomes with care",
    detail:
      "A sample view of consent-safe participation and verified learning outcomes.",
  },
};

const roleMetrics: Record<WorkspaceRole, Array<[string, string, string]>> = {
  client: [
    ["Active projects", "04", "+2 this month"],
    ["Decisions due", "02", "next 48 hours"],
    ["Funded value", "$18.4k", "+12% quarter"],
    ["Avg. response", "31h", "within target"],
  ],
  student: [
    ["Readiness", "58%", "+18% momentum"],
    ["Open projects", "08", "3 matched"],
    ["Practice hours", "14.5", "this month"],
    ["Verified wins", "03", "portfolio-ready"],
  ],
  lead: [
    ["Review queue", "06", "2 urgent"],
    ["Release confidence", "91%", "+6% this month"],
    ["Hours supervised", "42", "this cycle"],
    ["Escalations", "01", "needs context"],
  ],
  ops: [
    ["Pending approvals", "07", "-3 since Monday"],
    ["Open risks", "04", "1 high confidence"],
    ["Delivery flow", "31", "+14% week over week"],
    ["Exceptions", "02", "within response SLA"],
  ],
  admin: [
    ["Healthy providers", "08/09", "1 degraded"],
    ["Failed runs", "02", "retry available"],
    ["Access reviews", "12", "due this week"],
    ["Jobs recovered", "18", "+4 today"],
  ],
  university: [
    ["Participants", "126", "+22 this term"],
    ["Completed projects", "84", "67% completion"],
    ["Credentials", "71", "+11 this quarter"],
    ["Cohort privacy", "Safe", "threshold met"],
  ],
};

export function WorkspaceOverview({ role }: { role: WorkspaceRole }) {
  const [activeView, setActiveView] = useState<"signals" | "activity">(
    "signals",
  );
  const copy = roleCopy[role];
  const metrics = roleMetrics[role];
  const points =
    role === "student"
      ? demoWorkspaceSnapshot.trends.studentReadiness
      : role === "client"
        ? demoWorkspaceSnapshot.trends.clientDelivery
        : role === "university"
          ? demoWorkspaceSnapshot.trends.universityOutcomes
          : demoWorkspaceSnapshot.trends.operationsFlow;
  const maxValue = Math.max(...points.map((point) => point.value));

  return (
    <section
      className="overview-dashboard"
      aria-label={`${role} overview insights`}
    >
      <div className="overview-dashboard-header">
        <div>
          <span className="career-kicker dark">{copy.eyebrow}</span>
          <h2>{copy.title}</h2>
          <p>{copy.detail}</p>
        </div>
        <span className="sample-badge">
          <Sparkles size={13} /> Sample data
        </span>
      </div>
      <div className="overview-metrics">
        {metrics.map(([label, value, change], index) => (
          <article className="overview-metric" key={label}>
            <span className="overview-metric-icon">
              {index === 0 ? (
                <BriefcaseBusiness size={16} />
              ) : index === 1 ? (
                <CircleAlert size={16} />
              ) : index === 2 ? (
                <BarChart3 size={16} />
              ) : (
                <CheckCircle2 size={16} />
              )}
            </span>
            <span className="metric-label">{label}</span>
            <strong>{value}</strong>
            <small>{change}</small>
          </article>
        ))}
      </div>
      <div className="overview-grid">
        <article className="overview-chart-card">
          <div className="overview-card-heading">
            <div>
              <span className="insight-label">Last six periods</span>
              <h3>
                {role === "student"
                  ? "Readiness momentum"
                  : role === "university"
                    ? "Verified outcomes"
                    : "Healthy delivery flow"}
              </h3>
            </div>
            <span className="trend-up">
              <ArrowUpRight size={14} /> trending up
            </span>
          </div>
          <div className="overview-chart" aria-label="Illustrative trend chart">
            {points.map((point) => (
              <div className="overview-bar-column" key={point.label}>
                <span className="overview-bar-value">{point.value}</span>
                <span
                  className="overview-bar"
                  style={{
                    height: `${Math.max(18, (point.value / maxValue) * 100)}%`,
                  }}
                />
                <small>{point.label}</small>
              </div>
            ))}
          </div>
        </article>
        <article className="overview-activity-card">
          <div className="overview-card-heading">
            <div>
              <span className="insight-label">Fictional timeline</span>
              <h3>Recent activity</h3>
            </div>
            <div
              className="segmented-control compact"
              role="group"
              aria-label="Overview panel"
            >
              <button
                aria-pressed={activeView === "signals"}
                className={activeView === "signals" ? "selected" : ""}
                onClick={() => setActiveView("signals")}
                type="button"
              >
                Signals
              </button>
              <button
                aria-pressed={activeView === "activity"}
                className={activeView === "activity" ? "selected" : ""}
                onClick={() => setActiveView("activity")}
                type="button"
              >
                Activity
              </button>
            </div>
          </div>
          {activeView === "signals" ? (
            <div className="signal-list">
              <div>
                <ShieldCheck size={16} />
                <span>
                  <strong>Trust gates intact</strong>
                  <small>Human approval remains the next authority</small>
                </span>
              </div>
              <div>
                <Clock3 size={16} />
                <span>
                  <strong>Two next actions</strong>
                  <small>Both are inside the current response window</small>
                </span>
              </div>
              <div>
                <Users size={16} />
                <span>
                  <strong>People are in the loop</strong>
                  <small>Reviewers and participants have visible context</small>
                </span>
              </div>
            </div>
          ) : (
            <div className="activity-list">
              {demoWorkspaceSnapshot.activity.slice(0, 3).map((item) => (
                <div key={item.id} className={`activity-item ${item.tone}`}>
                  <span className="activity-dot" aria-hidden="true" />
                  <span>
                    <strong>{item.title}</strong>
                    <small>
                      {item.detail} · {item.time}
                    </small>
                  </span>
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
      <div className="overview-footnote">
        <GraduationCap size={15} /> Fictional demo metrics are illustrative and
        never represent live financial, academic, or operational decisions.
      </div>
    </section>
  );
}
