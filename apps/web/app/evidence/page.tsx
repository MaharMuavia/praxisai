import type { Metadata } from "next";
import {
  CheckCircle2,
  FlaskConical,
  GitBranch,
  ShieldAlert,
} from "lucide-react";
import { DemoNotice } from "@/components/demo-boundary";
import { MarketingFooter } from "@/components/marketing-footer";
import { MarketingNav } from "@/components/marketing-nav";
import { Card, SectionHeader } from "@/components/ui";

export const metadata: Metadata = {
  title: "Evidence map",
  description:
    "What PraxisAI implements, verifies, demonstrates, and leaves open.",
};

const evidenceGroups = [
  {
    title: "Implemented in the repository",
    icon: GitBranch,
    tone: "success",
    items: [
      "Role-aware workspace routes and project state transitions",
      "Deterministic quote, eligibility, approval, evidence, and credential boundaries",
      "Structured agent-run records with policy and approval metadata",
      "Accessible marketing navigation, responsive layouts, and reduced-motion handling",
    ],
  },
  {
    title: "CI verified",
    icon: CheckCircle2,
    tone: "success",
    items: [
      "TypeScript strict checks and ESLint",
      "Frontend unit and interaction coverage",
      "API tests, migrations, and contract-generated client checks",
      "Production builds and end-to-end route coverage when the CI environment is available",
    ],
  },
  {
    title: "Demonstrated with fixture data",
    icon: FlaskConical,
    tone: "ai",
    items: [
      "The `/judge` 14-step scenario",
      "Sanitized product preview panels and role journey records",
      "Demo workspace snapshots and illustrative dashboard trends",
      "Fixture AI proposals that never mutate production state",
    ],
  },
  {
    title: "Requires external production verification",
    icon: ShieldAlert,
    tone: "warning",
    items: [
      "Live Gemini credentials, model behavior, and provider quotas",
      "Payment provider webhooks and settlement reconciliation",
      "Production deployment, domain configuration, and observability",
      "Real customer outcomes, participant outcomes, and any future traction claims",
    ],
  },
] as const;

export default function EvidencePage() {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="content-page-hero evidence-hero">
        <div className="marketing-container content-page-hero-inner">
          <p className="marketing-eyebrow">Truthful by construction</p>
          <h1>Evidence before assertion.</h1>
          <p>
            Use this map to distinguish what the current repository implements,
            what verification covers, what the demo illustrates, and what is
            intentionally not claimed.
          </p>
          <DemoNotice>
            Demo labels describe fixture records only; they are not customer or
            traction claims.
          </DemoNotice>
        </div>
      </section>
      <section className="marketing-section">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="Four provenance buckets"
            title="A judge should never have to guess what a screen proves."
            description="The product separates code-backed behavior, automated verification, deterministic demonstration, and external dependencies."
          />
          <div className="evidence-map-grid">
            {evidenceGroups.map(({ title, icon: Icon, tone, items }) => (
              <Card
                className={`evidence-map-card evidence-map-${tone}`}
                key={title}
              >
                <div className="evidence-map-card-head">
                  <Icon size={21} aria-hidden="true" />
                  <span>{title}</span>
                </div>
                <ul>
                  {items.map((item) => (
                    <li key={item}>
                      <CheckCircle2 size={15} aria-hidden="true" />
                      {item}
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </div>
      </section>
      <section className="marketing-section marketing-section-muted">
        <div className="marketing-container evidence-review-note">
          <div>
            <p className="marketing-eyebrow">Review protocol</p>
            <h2>
              Start with the walkthrough, then inspect the source boundary.
            </h2>
          </div>
          <p>
            Open the judge walkthrough first for the product narrative. Use this
            page to challenge claims. If a capability depends on an external
            provider, deployment, secret, or human operating procedure, it stays
            in the final bucket until that check is performed.
          </p>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}
