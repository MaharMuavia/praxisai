import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  Fingerprint,
  GraduationCap,
  Landmark,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { MarketingFooter } from "./marketing-footer";
import { MarketingNav } from "./marketing-nav";
import { Button } from "./ui";
import { PublicIntakeForm } from "./public-intake-form";

export function ContentPage({
  title,
  eyebrow,
  description,
  points,
  path = "",
}: {
  title: string;
  eyebrow: string;
  description: string;
  points: string[];
  path?: string;
}) {
  const kind = path.startsWith("trust")
    ? "trust"
    : path.startsWith("solutions") || path === "solutions"
      ? "solutions"
      : path.includes("student")
        ? "student"
        : path.includes("compan") || path.includes("client")
          ? "company"
          : path.includes("university")
            ? "university"
            : path === "pricing"
              ? "pricing"
              : path === "contact"
                ? "contact"
                : "default";
  const visual =
    kind === "trust" ? (
      <EvidenceVisual />
    ) : kind === "solutions" ? (
      <SolutionsVisual />
    ) : kind === "student" ? (
      <StudentVisual />
    ) : kind === "company" ? (
      <CompanyVisual />
    ) : kind === "university" ? (
      <UniversityVisual />
    ) : kind === "pricing" ? (
      <PricingVisual />
    ) : kind === "contact" ? (
      <ContactVisual />
    ) : (
      <DefaultVisual />
    );
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="content-page-hero">
        <div className="marketing-container content-page-hero-inner">
          <p className="marketing-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
          <div className="content-page-hero-visual">{visual}</div>
        </div>
      </section>
      <section className="marketing-section content-page-body">
        <div className="marketing-container content-page-grid">
          <div>
            <p className="marketing-eyebrow">The PraxisAI approach</p>
            <h2>Clear boundaries make useful work possible.</h2>
            <p className="content-page-intro">
              This page describes the operating model and the commitments
              supported by the current product and policy surface. Where a
              workflow still needs backend support, the next step is stated
              plainly.
            </p>
          </div>
          <div className="content-page-points">
            {points.map((point, index) => (
              <article key={point}>
                <span className="content-point-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <CheckCircle2 size={19} aria-hidden="true" />
                <p>{point}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <RouteExperience path={path} />
      <section className="marketing-section content-page-cta">
        <div className="marketing-container">
          <h2>Choose a path into the studio.</h2>
          <p>
            Read the role-specific journey, or sign in to an existing workspace
            when your organization has been onboarded.
          </p>
          <div className="marketing-actions">
            <Button href="/for-students" variant="secondary">
              For students <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-companies" variant="primary">
              For companies <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}

function RouteExperience({ path }: { path: string }) {
  if (path === "for-students") {
    return (
      <section className="marketing-section route-experience route-experience-student">
        <div className="marketing-container">
          <p className="marketing-eyebrow">The student pathway</p>
          <h2>Practice → evidence → an offer you can understand.</h2>
          <div className="route-experience-grid">
            {[
              [
                "01",
                "Build evidence",
                "Complete practical briefs with feedback, tests, and handoff notes.",
              ],
              [
                "02",
                "Review readiness",
                "See the evidence a reviewer can use; there is no hidden frontend score.",
              ],
              [
                "03",
                "Choose transparently",
                "Compare scope, hours, pay, supervision, revisions, and portfolio terms.",
              ],
              [
                "04",
                "Appeal when needed",
                "Human support remains available for QA, payment, credential, and reputation decisions.",
              ],
            ].map(([number, title, detail]) => (
              <article className="route-step-card" key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{detail}</p>
              </article>
            ))}
          </div>
          <div className="route-faq">
            <h3>Student questions</h3>
            <details>
              <summary>Do I pay to access work or credentials?</summary>
              <p>
                No. Access to opportunities and the base earned credential is
                not sold to students.
              </p>
            </details>
            <details>
              <summary>What if I decline an offer?</summary>
              <p>
                Declining or allowing an offer to expire does not create a
                reputation penalty.
              </p>
            </details>
          </div>
        </div>
      </section>
    );
  }

  if (path === "for-companies") {
    return (
      <section className="marketing-section route-experience route-experience-company">
        <div className="marketing-container">
          <p className="marketing-eyebrow">The managed-delivery path</p>
          <h2>A bounded project with a visible owner at every handoff.</h2>
          <div className="route-experience-grid">
            {[
              [
                "Brief",
                "You bring the business problem, users, constraints, data sensitivity, and acceptance owner.",
              ],
              [
                "Scope",
                "PraxisAI turns context into reviewable deliverables, assumptions, and a quote.",
              ],
              [
                "Supervise",
                "An expert lead and coordinator keep decisions, risks, and QA findings visible.",
              ],
              [
                "Release",
                "You accept the agreed deliverable; new work uses a priced change order.",
              ],
            ].map(([title, detail]) => (
              <article className="route-step-card" key={title}>
                <h3>{title}</h3>
                <p>{detail}</p>
              </article>
            ))}
          </div>
          <div className="route-boundary-grid">
            <div>
              <strong>Suitable</strong>
              <p>
                Bounded websites, internal tools, dashboards, QA, data work, and
                workflow automation.
              </p>
            </div>
            <div>
              <strong>Not suitable</strong>
              <p>
                Safety-critical, surveillance, deceptive, illegal,
                academic-cheating, or unbounded builds.
              </p>
            </div>
          </div>
          <div className="marketing-actions">
            <Button href="/login" variant="primary">
              Start with an authenticated project brief{" "}
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      </section>
    );
  }

  if (path === "pricing") {
    return (
      <section className="marketing-section route-experience route-experience-pricing">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Commercial model</p>
          <h2>Terms are itemized before anyone accepts the work.</h2>
          <div className="pricing-ledger">
            {[
              [
                "Student compensation",
                "Shown as gross pay and expected hours in the offer.",
              ],
              [
                "Technical-lead compensation",
                "Shown separately for qualified supervision and review.",
              ],
              [
                "Platform service fee",
                "Shown as its own line rather than hidden in contributor pay.",
              ],
              [
                "Taxes and provider fees",
                "Included only when configured and disclosed for the project.",
              ],
              [
                "Revisions and change orders",
                "The base allowance is stated; materially new work is priced before release.",
              ],
            ].map(([title, detail]) => (
              <div key={title}>
                <strong>{title}</strong>
                <span>{detail}</span>
              </div>
            ))}
          </div>
          <p className="route-disclaimer">
            Illustrative examples on this site are nonbinding demo examples.
            PraxisAI does not publish a universal rate card until one is
            approved and configured.
          </p>
        </div>
      </section>
    );
  }

  if (path === "trust") {
    return (
      <section className="marketing-section route-experience route-experience-trust">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Authority map</p>
          <h2>AI can propose. People and deterministic services decide.</h2>
          <div className="trust-authority-grid">
            <div>
              <strong>AI may assist</strong>
              <p>
                Draft scope, summarize records, suggest matches, and surface QA
                findings with sources.
              </p>
            </div>
            <div>
              <strong>Humans approve</strong>
              <p>
                Scope, staffing, releases, disputes, payouts, credentials, and
                other consequential transitions.
              </p>
            </div>
            <div>
              <strong>Evidence stays distinct</strong>
              <p>
                Payment evidence is not client acceptance; a model proposal is
                not workflow authority.
              </p>
            </div>
            <div>
              <strong>Protection remains explicit</strong>
              <p>
                Consent, privacy boundaries, appeals, and credential
                verification are part of the product contract.
              </p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (path === "impact") {
    return (
      <section className="marketing-section route-experience route-experience-impact">
        <div className="marketing-container">
          <p className="marketing-eyebrow">
            Measurement without invented outcomes
          </p>
          <h2>When impact is reported, the evidence will be inspectable.</h2>
          <div className="impact-measurement-grid">
            {[
              [
                "Definition",
                "What the metric means and which records qualify.",
              ],
              [
                "Source",
                "Which approved operational or consented evidence produced it.",
              ],
              [
                "Exclusions",
                "Demo records, suppressed cohorts, and unconsented evidence stay out.",
              ],
              [
                "Safeguards",
                "Privacy thresholds, time windows, and approval state accompany the result.",
              ],
            ].map(([title, detail]) => (
              <article key={title}>
                <strong>{title}</strong>
                <p>{detail}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (path === "about") {
    return (
      <section className="marketing-section route-experience route-experience-about">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Why PraxisAI exists</p>
          <h2>
            Connect preparation to real work without hiding the boundaries.
          </h2>
          <div className="about-principles">
            {[
              "Practice is useful when it produces evidence, not just completion marks.",
              "Companies deserve a managed delivery model with accountable review.",
              "AI should make work more legible without becoming the authority.",
              "Responsible growth means pilots, governance, and evidence before scale claims.",
            ].map((principle) => (
              <p key={principle}>
                <CheckCircle2 size={18} aria-hidden="true" />
                {principle}
              </p>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (path === "contact") {
    return (
      <section className="marketing-section route-experience route-experience-contact">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Choose a supported path</p>
          <h2>Start where the current product can help.</h2>
          <div className="contact-path-grid">
            <Button href="/login" variant="primary">
              Company project brief <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-students" variant="secondary">
              Student pathway <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-expert-leads" variant="secondary">
              Expert lead pathway <ArrowRight size={16} aria-hidden="true" />
            </Button>
            <Button href="/for-universities" variant="secondary">
              University pathway <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
          <PublicIntakeForm />
        </div>
      </section>
    );
  }

  if (path.startsWith("solutions/")) {
    const solution = path.slice("solutions/".length).replaceAll("-", " ");
    return (
      <section className="marketing-section route-experience route-experience-solution">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Solution boundary</p>
          <h2>
            {solution.replace(/\b\w/g, (letter) => letter.toUpperCase())} is
            scoped around a decision, not a vague build.
          </h2>
          <div className="solution-boundary-grid">
            <div>
              <strong>Typical deliverables</strong>
              <p>
                Brief, route or workflow map, implemented surface, tests, review
                notes, and handoff evidence.
              </p>
            </div>
            <div>
              <strong>Client responsibilities</strong>
              <p>
                Provide access, source context, decision-makers, timely
                feedback, and acceptance criteria.
              </p>
            </div>
            <div>
              <strong>Unsupported use</strong>
              <p>
                Unbounded product builds, consequential automation without human
                approval, and work outside pilot boundaries.
              </p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return null;
}

function VisualFrame({ children }: { children: React.ReactNode }) {
  return <div className="content-visual-frame">{children}</div>;
}

function DefaultVisual() {
  return (
    <VisualFrame>
      <div className="visual-orbit" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <strong>Operational clarity</strong>
      <small>One place for the next accountable step.</small>
    </VisualFrame>
  );
}

function EvidenceVisual() {
  return (
    <VisualFrame>
      <div className="evidence-visual-chain">
        {[
          [Fingerprint, "Input hash"],
          [ClipboardCheck, "QA finding"],
          [ShieldCheck, "Human release"],
          [CheckCircle2, "Acceptance"],
        ].map(([Icon, label]) => (
          <div key={label as string}>
            <Icon size={17} aria-hidden="true" />
            <span>{label as string}</span>
          </div>
        ))}
      </div>
      <small>Records remain distinct and connected.</small>
    </VisualFrame>
  );
}

function SolutionsVisual() {
  return (
    <VisualFrame>
      <div className="solution-visual-board">
        <span>Brief</span>
        <i />
        <span>Scope</span>
        <i />
        <span>Release</span>
      </div>
      <small>Bounded projects with a reviewable outcome.</small>
    </VisualFrame>
  );
}

function StudentVisual() {
  return (
    <VisualFrame>
      <div className="visual-timeline">
        {["Practice", "Readiness", "Offer", "Proof"].map((item, index) => (
          <div key={item}>
            <span>{index + 1}</span>
            <strong>{item}</strong>
          </div>
        ))}
      </div>
      <small>Practice → paid work → verifiable experience.</small>
    </VisualFrame>
  );
}

function CompanyVisual() {
  return (
    <VisualFrame>
      <div className="company-visual-ledger">
        <div>
          <ClipboardCheck size={17} />
          <span>Scope owner</span>
          <b>Coordinator</b>
        </div>
        <div>
          <Landmark size={17} />
          <span>Delivery</span>
          <b>Supervised squad</b>
        </div>
        <div>
          <ShieldCheck size={17} />
          <span>Release</span>
          <b>Client acceptance</b>
        </div>
      </div>
      <small>Managed delivery, not an open marketplace.</small>
    </VisualFrame>
  );
}

function UniversityVisual() {
  return (
    <VisualFrame>
      <div className="university-visual">
        <GraduationCap size={21} />
        <div>
          <strong>Purpose-limited report</strong>
          <small>Consent · cohort threshold · expiry</small>
        </div>
      </div>
      <small>Individual records stay outside the aggregate view.</small>
    </VisualFrame>
  );
}

function PricingVisual() {
  return (
    <VisualFrame>
      <div className="pricing-visual">
        <WalletCards size={20} />
        <div>
          <span>Offer ledger</span>
          <strong>Pay + hours + revisions</strong>
          <small>Visible before acceptance</small>
        </div>
      </div>
      <small>Commercial terms are evidence, not a surprise.</small>
    </VisualFrame>
  );
}

function ContactVisual() {
  return (
    <VisualFrame>
      <div className="contact-visual">
        <span>01</span>
        <strong>Choose a supported path</strong>
        <span>02</span>
        <strong>Bring the right context</strong>
        <span>03</span>
        <strong>Confirm the next action</strong>
      </div>
      <small>
        Public intake remains truthful until a real endpoint exists.
      </small>
    </VisualFrame>
  );
}
