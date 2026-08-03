"use client";

import {
  ArrowLeft,
  ArrowRight,
  Check,
  ClipboardCheck,
  Copy,
  Expand,
  FileCheck2,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { DemoBadge, DemoNotice } from "@/components/demo-boundary";
import { Button } from "@/components/ui";

type Step = {
  role: string;
  title: string;
  input: string;
  action: string;
  result: string;
  audit: string;
  boundary: string;
  icon: typeof ClipboardCheck;
};

const steps: Step[] = [
  {
    role: "Company owner",
    title: "Submit a bounded project brief",
    input: "Northstar Civic Studio needs a searchable resource directory.",
    action:
      "The company states the outcome, constraints, and acceptance owner.",
    result: "A project intake is created with a clear delivery boundary.",
    audit: "Brief version · owner · acceptance criteria",
    boundary: "No team or payment commitment is created yet.",
    icon: ClipboardCheck,
  },
  {
    role: "Fixture AI",
    title: "Draft scope assumptions",
    input: "The structured proposal uses the brief and its stated constraints.",
    action: "Fixture AI suggests assumptions, milestones, and open questions.",
    result: "A reviewable scope proposal is ready for a coordinator.",
    audit: "Input hash · proposal version · source references",
    boundary: "AI proposes; it cannot accept scope or change project state.",
    icon: Sparkles,
  },
  {
    role: "Coordinator",
    title: "Review scope and quote",
    input: "The proposal includes hours, roles, risks, and revision rounds.",
    action:
      "The coordinator checks feasibility and deterministic pricing rules.",
    result: "The client receives a bounded quote for a human decision.",
    audit: "Reviewer · decision reason · quote snapshot",
    boundary: "The quote is a proposal until the client accepts it.",
    icon: ShieldCheck,
  },
  {
    role: "Company owner",
    title: "Accept terms and fund externally",
    input: "The company sees scope, hours, compensation, and acceptance rules.",
    action: "The owner accepts the terms and provides funding evidence.",
    result: "The project is ready for staffing without hidden obligations.",
    audit: "Terms version · consent · funding evidence reference",
    boundary:
      "This walkthrough simulates funding evidence; no provider is called.",
    icon: Check,
  },
  {
    role: "Coordinator",
    title: "Run deterministic eligibility checks",
    input:
      "Candidate records include declared skills, readiness, and conflicts.",
    action: "Rules filter candidates against the accepted project boundary.",
    result: "Eligible candidates are available for supervised matching.",
    audit: "Rule set version · candidate set · conflict checks",
    boundary: "Eligibility is deterministic; AI does not decide access.",
    icon: Users,
  },
  {
    role: "Fixture AI",
    title: "Suggest a delivery plan",
    input:
      "The accepted criteria and dependencies are visible to the proposal run.",
    action: "Fixture AI drafts milestones and task sequencing.",
    result: "A plan proposal is ready for lead and coordinator review.",
    audit: "Plan version · criteria coverage · confidence signals",
    boundary: "The plan is not active until a human approves it.",
    icon: Sparkles,
  },
  {
    role: "Expert lead",
    title: "Approve the supervised plan",
    input: "The lead sees dependencies, estimates, and role boundaries.",
    action:
      "The lead confirms the plan is safe and understandable to the squad.",
    result: "Tasks are created inside the approved project state.",
    audit: "Lead approval · scope version · milestone record",
    boundary: "The lead owns delivery quality, not financial authorization.",
    icon: ShieldCheck,
  },
  {
    role: "Student squad",
    title: "Deliver against accepted criteria",
    input: "The squad works from visible tasks, feedback, and due dates.",
    action: "Students submit work and the lead records reviewable feedback.",
    result: "A release candidate and contribution evidence are assembled.",
    audit: "Task history · feedback · contribution record",
    boundary: "Student work is supervised and remains attributable.",
    icon: Users,
  },
  {
    role: "Fixture AI",
    title: "Surface QA findings",
    input:
      "The release candidate and acceptance criteria are provided as inputs.",
    action: "Fixture AI drafts structured QA findings for human review.",
    result: "Findings are categorized as blockers, warnings, or passes.",
    audit: "Evidence references · finding severity · run identifier",
    boundary: "AI reports findings; a human decides release readiness.",
    icon: FileCheck2,
  },
  {
    role: "Expert lead",
    title: "Record release approval",
    input: "The lead reviews QA findings and the acceptance evidence.",
    action: "The lead records a release decision with a reason.",
    result: "The client can inspect the approved release evidence.",
    audit: "Release decision · approver · decision reason",
    boundary: "Release approval is a human action and remains append-only.",
    icon: Check,
  },
  {
    role: "Company owner",
    title: "Accept the delivered outcome",
    input: "The company compares the release with the original criteria.",
    action: "The owner accepts the delivery or records a specific dispute.",
    result: "Acceptance is distinct from QA and is visible to all parties.",
    audit: "Client decision · acceptance timestamp · evidence links",
    boundary: "A dispute routes to review; it does not silently alter history.",
    icon: ClipboardCheck,
  },
  {
    role: "Operations",
    title: "Reconcile the evidence chain",
    input:
      "The accepted release, offer terms, and contribution records are linked.",
    action:
      "Operations checks that the records agree before compensation is approved.",
    result:
      "A complete project record is ready for the final operational decision.",
    audit: "Evidence links · record versions · reconciliation result",
    boundary:
      "Reconciliation detects gaps; it cannot rewrite append-only records.",
    icon: FileCheck2,
  },
  {
    role: "Operations",
    title: "Record approved compensation",
    input: "Offer terms, hours, and acceptance records are complete.",
    action: "Operations verifies the deterministic payout record.",
    result: "Compensation evidence is visible without exposing private data.",
    audit: "Offer version · approval · payout evidence",
    boundary:
      "This scenario does not move money or claim live payment success.",
    icon: ShieldCheck,
  },
  {
    role: "Student",
    title: "Control portfolio and credential proof",
    input: "The student reviews the accepted evidence and sharing terms.",
    action: "The student consents to the proof they want to share.",
    result: "A credential record can point to consented project evidence.",
    audit: "Consent record · evidence scope · credential status",
    boundary:
      "Credentials are evidence-backed; they are not fabricated outcomes.",
    icon: FileCheck2,
  },
];

export function JudgeWalkthrough() {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [copied, setCopied] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const active = steps[index];
  const Icon = active.icon;

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      setReducedMotion(media.matches);
      if (media.matches) setPlaying(false);
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!playing || reducedMotion) return;
    const timer = window.setInterval(() => {
      setIndex((current) => {
        if (current === steps.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 4800);
    return () => window.clearInterval(timer);
  }, [playing, reducedMotion]);

  const select = (next: number) => {
    setIndex(Math.max(0, Math.min(steps.length - 1, next)));
    setPlaying(false);
  };

  async function copyLink() {
    if (!navigator.clipboard) return;
    await navigator.clipboard.writeText(`${window.location.origin}/judge`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  async function toggleFullscreen() {
    if (!rootRef.current) return;
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else if (rootRef.current.requestFullscreen) {
      await rootRef.current.requestFullscreen();
    }
  }

  return (
    <div
      ref={rootRef}
      className="judge-walkthrough"
      role="application"
      onKeyDown={(event) => {
        if (event.key === "ArrowRight") {
          event.preventDefault();
          select(index + 1);
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          select(index - 1);
        } else if (event.key === "Home") {
          event.preventDefault();
          select(0);
        } else if (event.key === "End") {
          event.preventDefault();
          select(steps.length - 1);
        }
      }}
      tabIndex={0}
      aria-label="Interactive PraxisAI judge walkthrough"
    >
      <div className="judge-walkthrough-head">
        <div>
          <p className="marketing-eyebrow">14-step product walkthrough</p>
          <h2>One project. Four authorities. A complete evidence chain.</h2>
        </div>
        <DemoNotice>
          Fixture AI and simulated workflow; no live provider calls.
        </DemoNotice>
      </div>
      <div
        className="judge-progress"
        aria-label={`Step ${index + 1} of ${steps.length}`}
      >
        <span style={{ width: `${((index + 1) / steps.length) * 100}%` }} />
      </div>
      <div className="judge-walkthrough-layout">
        <aside className="judge-step-list" aria-label="Walkthrough steps">
          {steps.map((step, stepIndex) => (
            <button
              className={stepIndex === index ? "is-active" : ""}
              type="button"
              key={step.title}
              aria-current={stepIndex === index ? "step" : undefined}
              onClick={() => select(stepIndex)}
            >
              <span>{String(stepIndex + 1).padStart(2, "0")}</span>
              <strong>{step.title}</strong>
            </button>
          ))}
        </aside>
        <section className="judge-step-panel" aria-live="polite">
          <div className="judge-step-panel-topline">
            <DemoBadge>Demo environment</DemoBadge>
            <span>
              Step {index + 1} / {steps.length}
            </span>
          </div>
          <div className="judge-step-title">
            <span className="judge-step-icon">
              <Icon size={21} aria-hidden="true" />
            </span>
            <div>
              <p>{active.role}</p>
              <h3>{active.title}</h3>
            </div>
          </div>
          <div className="judge-step-facts">
            <div>
              <span>Input</span>
              <strong>{active.input}</strong>
            </div>
            <div>
              <span>Action</span>
              <strong>{active.action}</strong>
            </div>
            <div>
              <span>Result</span>
              <strong>{active.result}</strong>
            </div>
          </div>
          <div className="judge-audit-row">
            <span>
              <FileCheck2 size={16} aria-hidden="true" /> Recorded evidence
            </span>
            <strong>{active.audit}</strong>
          </div>
          <p className="judge-boundary">
            <ShieldCheck size={16} aria-hidden="true" /> {active.boundary}
          </p>
        </section>
      </div>
      <div className="judge-controls">
        <div className="judge-controls-primary">
          <Button
            variant="secondary"
            onClick={() => select(index - 1)}
            disabled={index === 0}
            ariaLabel="Previous step"
          >
            <ArrowLeft size={16} /> Previous
          </Button>
          <Button
            variant="primary"
            onClick={() => select(index + 1)}
            disabled={index === steps.length - 1}
            ariaLabel="Next step"
          >
            Next <ArrowRight size={16} />
          </Button>
          <button
            className="judge-icon-button"
            type="button"
            onClick={() => setPlaying((value) => !value)}
            disabled={reducedMotion}
            aria-label={playing ? "Pause walkthrough" : "Play walkthrough"}
          >
            {playing ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <button
            className="judge-icon-button"
            type="button"
            onClick={() => select(0)}
            aria-label="Restart walkthrough"
          >
            <RotateCcw size={16} />
          </button>
        </div>
        <div className="judge-controls-secondary">
          <button
            className="judge-text-button"
            type="button"
            onClick={() => void copyLink()}
          >
            <Copy size={15} /> {copied ? "Copied" : "Copy link"}
          </button>
          <button
            className="judge-text-button"
            type="button"
            onClick={() => void toggleFullscreen()}
          >
            <Expand size={15} /> Fullscreen
          </button>
          <Link className="judge-exit-link" href="/for-companies">
            Explore the full product <X size={14} aria-hidden="true" />
          </Link>
        </div>
      </div>
      <p className="judge-keyboard-hint">
        Keyboard: Left/Right to move · Home/End to jump · Tab to reach controls
      </p>
    </div>
  );
}
