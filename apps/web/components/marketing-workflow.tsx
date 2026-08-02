"use client";

import {
  BadgeCheck,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  ClipboardCheck,
  Pause,
  Play,
  Sparkles,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnimatedPresencePanel, WorkflowMotion } from "./motion";
import { StatusBadge } from "./ui";

const workflow = [
  {
    label: "Company brief",
    detail: "Outcome, constraints, and acceptance criteria",
    icon: ClipboardCheck,
    actor: "Company + coordinator",
    evidence: "A bounded brief with an accountable owner",
  },
  {
    label: "AI-assisted scope",
    detail: "Structured assumptions for human review",
    icon: Sparkles,
    actor: "AI proposes; policy checks",
    evidence: "Versioned assumptions and source references",
  },
  {
    label: "Student preparation",
    detail: "Practice evidence and readiness signals",
    icon: BookOpen,
    actor: "Student + learning coach",
    evidence: "Reviewed practice artifacts and feedback",
  },
  {
    label: "Supervised squad",
    detail: "Qualified people with an expert lead",
    icon: Users,
    actor: "Coordinator + expert lead",
    evidence: "Role boundaries, conflicts, and delivery plan",
  },
  {
    label: "Verified delivery",
    detail: "QA, acceptance, and evidence trail",
    icon: BadgeCheck,
    actor: "Lead + client",
    evidence: "QA findings, release approval, and acceptance",
  },
  {
    label: "Paid experience",
    detail: "Visible terms and approved compensation",
    icon: CircleDollarSign,
    actor: "Operations + payment provider",
    evidence: "Offer terms, payout evidence, and credential record",
  },
];

export function MarketingWorkflow() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const active = workflow[activeIndex];
  const ActiveIcon = active.icon;

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      setReducedMotion(media.matches);
      if (media.matches) setAutoPlay(false);
    };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const node = rootRef.current;
    if (!node || reducedMotion) return;
    const observer = new IntersectionObserver(
      ([entry]) => setAutoPlay(entry.isIntersecting),
      { threshold: 0.2 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [reducedMotion]);

  useEffect(() => {
    if (!autoPlay || reducedMotion) return;
    const timer = window.setInterval(
      () => setActiveIndex((current) => (current + 1) % workflow.length),
      4200,
    );
    return () => window.clearInterval(timer);
  }, [autoPlay, reducedMotion]);

  const choose = (index: number) => {
    setActiveIndex(index);
    setAutoPlay(false);
  };
  const move = (delta: number) =>
    choose((activeIndex + delta + workflow.length) % workflow.length);

  return (
    <div ref={rootRef}>
      <WorkflowMotion
        className="workflow-visual"
        aria-label="PraxisAI operating workflow"
      >
        <div className="workflow-visual-head">
          <div>
            <span className="workflow-kicker">Operating model</span>
            <strong>From brief to proof</strong>
          </div>
          <StatusBadge tone="ai">Conceptual workflow</StatusBadge>
        </div>
        <div className="workflow-path" aria-hidden="true">
          <span
            style={{
              transform: `scaleX(${activeIndex / (workflow.length - 1)})`,
            }}
          />
        </div>
        <div className="workflow-steps">
          {workflow.map((step, index) => {
            const Icon = step.icon;
            return (
              <button
                className={`workflow-step ${activeIndex === index ? "is-active" : ""}`}
                key={step.label}
                type="button"
                aria-pressed={activeIndex === index}
                onClick={() => choose(index)}
              >
                <span className="workflow-index">0{index + 1}</span>
                <span className="workflow-icon">
                  <Icon size={17} aria-hidden="true" />
                </span>
                <span className="workflow-step-copy">
                  <strong>{step.label}</strong>
                  <small>{step.detail}</small>
                </span>
                <ChevronRight size={16} aria-hidden="true" />
              </button>
            );
          })}
        </div>
        <AnimatedPresencePanel
          className="workflow-detail"
          panelKey={active.label}
        >
          <div className="workflow-detail-icon">
            <ActiveIcon size={19} aria-hidden="true" />
          </div>
          <div aria-live="polite">
            <span>Selected stage · {active.actor}</span>
            <strong>{active.label}</strong>
            <p>{active.detail}</p>
            <small className="workflow-evidence">
              Recorded: {active.evidence}
            </small>
          </div>
        </AnimatedPresencePanel>
        <div className="workflow-controls">
          <span>
            {autoPlay && !reducedMotion
              ? "Auto sequence · pauses when offscreen"
              : "Manual review mode"}
          </span>
          <div>
            <button
              type="button"
              className="workflow-control"
              onClick={() => move(-1)}
              aria-label="Previous workflow stage"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className="workflow-control"
              onClick={() => setAutoPlay((value) => !value)}
              aria-label={
                autoPlay ? "Pause workflow sequence" : "Play workflow sequence"
              }
            >
              {autoPlay ? <Pause size={15} /> : <Play size={15} />}
            </button>
            <button
              type="button"
              className="workflow-control"
              onClick={() => move(1)}
              aria-label="Next workflow stage"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </WorkflowMotion>
    </div>
  );
}
