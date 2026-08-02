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
