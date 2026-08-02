"use client";

import {
  Activity,
  Check,
  ClipboardCheck,
  Code2,
  FileSearch,
  GraduationCap,
  ShieldCheck,
  Sparkles,
  WalletCards,
} from "lucide-react";
import { useState } from "react";
import { AnimatedPresencePanel, Reveal } from "./motion";
import { StatusBadge } from "./ui";

type Preview = {
  label: string;
  icon: typeof Activity;
  title: string;
  summary: string;
  status: string;
  statusTone: "neutral" | "success" | "warning" | "ai";
  rows: Array<[string, string]>;
};

const previews: Preview[] = [
  {
    label: "Project intake",
    icon: ClipboardCheck,
    title: "Company project brief",
    summary:
      "A bounded brief keeps the outcome, constraints, and decision owner visible before a team is formed.",
    status: "Awaiting scope review",
    statusTone: "warning",
    rows: [
      ["Outcome", "Reduce manual weekly reporting"],
      ["Boundary", "One internal workflow"],
      ["Approval", "Coordinator review required"],
    ],
  },
  {
    label: "Readiness",
    icon: GraduationCap,
    title: "Student readiness evidence",
    summary:
      "Readiness is a reviewable set of work samples and feedback, not a hidden score or popularity signal.",
    status: "Evidence in review",
    statusTone: "success",
    rows: [
      ["Practice brief", "Workflow map · reviewed"],
      ["Feedback", "2 coaching notes"],
      ["Next step", "Complete validation exercise"],
    ],
  },
  {
    label: "Agent operations",
    icon: Sparkles,
    title: "Structured agent run",
    summary:
      "AI can draft a proposal, while policy checks and human approvals control any consequential change.",
    status: "Human approval required",
    statusTone: "ai",
    rows: [
      ["Goal", "Draft scope assumptions"],
      ["Policy", "No external side effects"],
      ["Evidence", "Input hash · sources · confidence"],
    ],
  },
  {
    label: "QA evidence",
    icon: FileSearch,
    title: "Release evidence chain",
    summary:
      "QA findings, release approval, client acceptance, and payout evidence stay distinct and traceable.",
    status: "Release review",
    statusTone: "success",
    rows: [
      ["QA", "3 findings · 0 blockers"],
      ["Release", "Lead approval recorded"],
      ["Payment", "Terms visible before acceptance"],
    ],
  },
];

export function MarketingProductPreview() {
  const [active, setActive] = useState(0);
  const preview = previews[active];
  const Icon = preview.icon;
  return (
    <section className="marketing-section marketing-product-section">
      <div className="marketing-container">
        <Reveal className="product-section-heading">
          <div>
            <p className="marketing-eyebrow">See how PraxisAI operates</p>
            <h2>The product makes the boundaries visible.</h2>
          </div>
          <p>
            Sanitized product demonstration data. These screens illustrate the
            operating model and are not customer records or traction claims.
          </p>
        </Reveal>
        <div className="product-preview-layout">
          <div
            className="product-preview-tabs"
            role="tablist"
            aria-label="Product experience previews"
          >
            {previews.map((item, index) => {
              const TabIcon = item.icon;
              return (
                <button
                  className={active === index ? "is-active" : ""}
                  key={item.label}
                  role="tab"
                  aria-selected={active === index}
                  aria-controls={`preview-panel-${index}`}
                  type="button"
                  onClick={() => setActive(index)}
                >
                  <TabIcon size={16} aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
          <AnimatedPresencePanel
            className="product-browser"
            panelKey={preview.label}
          >
            <div className="product-browser-bar">
              <span />
              <span />
              <span />
              <small>
                PraxisAI / workspace / {preview.label.toLowerCase()}
              </small>
            </div>
            <div
              className="product-browser-body"
              id={`preview-panel-${active}`}
              role="tabpanel"
              aria-label={preview.label}
            >
              <div className="product-preview-title">
                <div className="product-preview-icon">
                  <Icon size={18} aria-hidden="true" />
                </div>
                <div>
                  <span>Product demonstration</span>
                  <h3>{preview.title}</h3>
                </div>
                <StatusBadge tone={preview.statusTone}>
                  {preview.status}
                </StatusBadge>
              </div>
              <p className="product-preview-summary">{preview.summary}</p>
              <div className="product-preview-rows">
                {preview.rows.map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                    <Check size={15} aria-hidden="true" />
                  </div>
                ))}
              </div>
              <div className="product-preview-footer">
                <span>
                  <ShieldCheck size={15} aria-hidden="true" /> Evidence boundary
                  visible
                </span>
                <span>
                  <Code2 size={15} aria-hidden="true" /> Demo mode
                </span>
              </div>
            </div>
          </AnimatedPresencePanel>
        </div>
      </div>
    </section>
  );
}

export function MarketingPathways() {
  return (
    <section className="marketing-section marketing-pathways">
      <div className="marketing-container">
        <div className="pathways-heading">
          <p className="marketing-eyebrow">Two accountable journeys</p>
          <h2>Different roles. One managed delivery company.</h2>
        </div>
        <div className="pathway-grid">
          <article className="pathway-card pathway-card-student">
            <div className="pathway-card-head">
              <GraduationCap size={22} aria-hidden="true" />
              <span>Student pathway</span>
            </div>
            <h3>Build proof before you need to sell it.</h3>
            <div className="pathway-timeline">
              {[
                "Apply",
                "Diagnostic",
                "Practice",
                "Readiness",
                "Offer",
                "Supervised project",
                "Earnings + credential",
              ].map((item, index) => (
                <div key={item}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{item}</strong>
                </div>
              ))}
            </div>
            <p>
              No payment to access work. Clear pay and hours. Declining does not
              damage reputation. Human supervision and appeals remain part of
              the pathway.
            </p>
          </article>
          <article className="pathway-card pathway-card-company">
            <div className="pathway-card-head">
              <WalletCards size={22} aria-hidden="true" />
              <span>Company pathway</span>
            </div>
            <h3>Move from business problem to accepted release.</h3>
            <div className="pathway-timeline">
              {[
                "Submit brief",
                "Clarify need",
                "Review scope",
                "Approve terms",
                "Fund",
                "Track milestones",
                "Accept delivery",
              ].map((item, index) => (
                <div key={item}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{item}</strong>
                </div>
              ))}
            </div>
            <p>
              PraxisAI manages the project boundary, team review, supervision,
              QA, and release evidence. It is not an unrestricted marketplace.
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
