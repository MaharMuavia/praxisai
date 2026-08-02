"use client";

import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  Fingerprint,
  Scale,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { MarketingNav } from "./marketing-nav";

const steps = [
  [
    "Learn",
    "Practice briefs and evidence",
    "Ready",
    "Build the proof employers can actually evaluate.",
  ],
  [
    "Propose",
    "Approach, plan, price, proof",
    "Submitted",
    "Turn practice evidence into a clear, bounded proposal.",
  ],
  [
    "Select",
    "Employer decision and reason",
    "Chosen",
    "Compare people on evidence, not a vague profile or guess.",
  ],
  [
    "Deliver",
    "Supervision, QA, pay, credential",
    "Verified",
    "Carry the work through human review and verifiable release evidence.",
  ],
];

export function LandingPage() {
  const [activeStep, setActiveStep] = useState(0);
  const activeJourney = steps[activeStep];

  return (
    <main className="marketing-shell">
      <MarketingNav />
      <section className="hero">
        <div className="hero-grid">
          <div>
            <div className="eyebrow">
              Learn real skills. Win paid projects. Build verified experience.
            </div>
            <h1>
              From learning
              <br />
              <span>to paid delivery.</span>
            </h1>
            <p className="hero-copy">
              PraxisAI is a career and talent platform where students practice
              employer-relevant skills, prove their ability, submit professional
              proposals, and deliver supervised paid projects for real
              organizations.
            </p>
            <div className="hero-actions">
              <Link className="button button-accent" href="/login">
                Enter student workspace <ArrowRight size={17} />
              </Link>
              <Link
                className="button button-ghost"
                href="/how-it-works/clients"
              >
                Hire emerging talent
              </Link>
            </div>
          </div>
          <aside className="operations-card" aria-label="PraxisAI career loop">
            <div className="card-head">
              <div>
                <div className="eyebrow" style={{ color: "#61717c" }}>
                  Career-to-project journey
                </div>
                <strong>Accessible community platform</strong>
              </div>
              <span className="demo-badge">Demo data</span>
            </div>
            {steps.map(([name, detail, status], index) => (
              <button
                className={`loop-step ${activeStep === index ? "active" : ""}`}
                key={name}
                onClick={() => setActiveStep(index)}
                type="button"
              >
                <span className="step-number">0{index + 1}</span>
                <span>
                  <strong>{name}</strong>
                  <small>{detail}</small>
                </span>
                <span className="status-badge">{status}</span>
              </button>
            ))}
            <div className="journey-detail">
              <span className="eyebrow" style={{ color: "#26715d" }}>
                Selected stage · {activeJourney[0]}
              </span>
              <p>{activeJourney[3]}</p>
            </div>
          </aside>
        </div>
      </section>
      <div className="band">
        <span>
          Students build proof. Employers choose. Teams verify delivery.
        </span>
        <Fingerprint />
      </div>
      <section className="section marketplace-section">
        <div className="marketplace-heading">
          <div>
            <div className="eyebrow" style={{ color: "#26715d" }}>
              One connected career system
            </div>
            <h2 className="section-title">
              Training is useful when it leads to trusted work.
            </h2>
          </div>
          <p>
            Curriculum, work evidence, employer briefs, student proposals,
            supervised delivery, payment records, and credentials stay connected
            instead of living in separate tools.
          </p>
        </div>
        <div className="marketplace-flow">
          <article>
            <span>01</span>
            <BookOpen />
            <h3>Learn through practice</h3>
            <p>
              Structured paths teach requirements, implementation, testing, and
              professional delivery through exercises that produce reviewable
              evidence.
            </p>
          </article>
          <article>
            <span>02</span>
            <Send />
            <h3>Propose professionally</h3>
            <p>
              Students respond to complete employer briefs with an approach,
              milestone plan, relevant samples, availability, timing, and a
              fixed amount.
            </p>
          </article>
          <article>
            <span>03</span>
            <Building2 />
            <h3>Choose with evidence</h3>
            <p>
              Employers compare fit and proof, then record an accept or reject
              reason. Selection never authorizes unpaid or unfunded work.
            </p>
          </article>
          <article>
            <span>04</span>
            <BriefcaseBusiness />
            <h3>Deliver with support</h3>
            <p>
              Approved teams work against immutable scope with lead review, QA,
              client acceptance, pay protection, and verifiable contribution
              records.
            </p>
          </article>
        </div>
        <div className="landing-metrics" aria-label="PraxisAI sample metrics">
          <div>
            <span>126</span>
            <small>fictional participants</small>
          </div>
          <div>
            <span>84</span>
            <small>verified project completions</small>
          </div>
          <div>
            <span>91%</span>
            <small>sample release confidence</small>
          </div>
          <div>
            <span>0</span>
            <small>unpaid trial tasks</small>
          </div>
        </div>
      </section>
      <section className="section">
        <div className="eyebrow" style={{ color: "#26715d" }}>
          Built for accountable delivery
        </div>
        <h2 className="section-title">
          Professional experience needs more than a task and a badge.
        </h2>
        <div className="trust-grid">
          <article className="trust-card">
            <ShieldCheck className="icon" />
            <h3>No hidden work</h3>
            <p>
              Students see scope, budget, expected hours, deadline, supervision,
              proposal requirements, and portfolio terms before making a
              commitment.
            </p>
          </article>
          <article className="trust-card">
            <Scale className="icon" />
            <h3>Human authority</h3>
            <p>
              Employers, coordinators, and technical leads approve selection,
              scope, staffing, releases, appeals, payouts, and credential
              evidence.
            </p>
          </article>
          <article className="trust-card">
            <CheckCircle2 className="icon" />
            <h3>Verifiable outcomes</h3>
            <p>
              Client acceptance, structured QA evidence, payment records, and
              consented contributions support a signed credential.
            </p>
          </article>
        </div>
        <div className="landing-callout">
          <div className="landing-callout-icon">
            <Sparkles size={20} />
          </div>
          <div>
            <strong>Designed for the moment after “looks promising.”</strong>
            <p>
              PraxisAI keeps scope, decision reasons, supervision, QA, funding,
              and credential evidence connected so progress is visible before
              anyone calls work complete.
            </p>
          </div>
          <Link className="button button-primary" href="/trust">
            Explore the trust model <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </main>
  );
}
