import type { Metadata } from "next";
import { ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { DemoNotice } from "@/components/demo-boundary";
import { MarketingFooter } from "@/components/marketing-footer";
import { MarketingNav } from "@/components/marketing-nav";
import { Button, Card, SectionHeader } from "@/components/ui";
import { UnitEconomicsCalculator } from "@/components/unit-economics-calculator";

export const metadata: Metadata = {
  title: "Business model & Unit Economics",
  description:
    "An interactive view of the PraxisAI managed delivery economics and escrow ledger.",
};

const assumptions = [
  [
    "Illustrative client project",
    "$4,000",
    "A bounded project example, not a price quote or customer contract.",
  ],
  [
    "Illustrative delivery cost",
    "$2,800",
    "Student and lead compensation assumptions shown as an example.",
  ],
  [
    "Illustrative operating margin",
    "$1,200",
    "A planning assumption before taxes, support, and external costs.",
  ],
  [
    "Student access fee",
    "$0",
    "Students do not pay to access preparation or project opportunities.",
  ],
] as const;

export default function BusinessModelPage() {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="content-page-hero business-model-hero">
        <div className="marketing-container content-page-hero-inner">
          <p className="marketing-eyebrow">
            Sustainability with a protection boundary
          </p>
          <h1>
            Companies pay for managed delivery. Students earn through approved
            work.
          </h1>
          <p>
            The operating model is designed around bounded projects, visible
            terms, supervision, and evidence. Explore the interactive unit
            economics simulator below.
          </p>
          <DemoNotice>
            Interactive unit economics · Verified mathematical model · Not an
            unregistered securities offering or live investment contract
          </DemoNotice>
        </div>
      </section>

      {/* Interactive Simulator Section */}
      <section className="marketing-section" style={{ paddingTop: "1rem" }}>
        <div className="marketing-container">
          <SectionHeader
            eyebrow="Interactive Economics Simulator"
            title="Model project scale, student earnings, and AI efficiency."
            description="Adjust project volume, pricing, and student compensation splits to observe real-time gross merchandise value, direct earnings release, and negligible Gemini compute overhead."
          />
          <UnitEconomicsCalculator />
        </div>
      </section>

      <section className="marketing-section marketing-section-muted">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="Baseline planning assumptions"
            title="The boundary is as important as the split."
            description="A sustainable operation must make room for supervision, QA, support, and participant protection without charging students for access."
          />
          <div className="business-assumption-grid">
            {assumptions.map(([label, value, detail]) => (
              <Card key={label} className="business-assumption">
                <span>{label}</span>
                <strong>{value}</strong>
                <p>{detail}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="marketing-section">
        <div className="marketing-container business-model-grid">
          <div>
            <p className="marketing-eyebrow">Who pays for what</p>
            <h2>Commercial value and participant protection stay legible.</h2>
          </div>
          <div className="business-model-points">
            <p>
              <CheckCircle2 size={17} /> Companies pay for a managed path from a
              clear brief to accepted delivery.
            </p>
            <p>
              <CheckCircle2 size={17} /> Project terms show scope, hours,
              revisions, and compensation before acceptance.
            </p>
            <p>
              <CheckCircle2 size={17} /> Students do not pay a marketplace or
              credential access fee.
            </p>
            <p>
              <ShieldCheck size={17} /> Money, access, release, disputes, and
              credentials remain human-authorized.
            </p>
          </div>
        </div>
      </section>
      <section className="marketing-section marketing-final-cta">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Inspect the operating model</p>
          <h2>See the assumptions inside the full workflow.</h2>
          <div className="marketing-actions">
            <Button href="/judge" variant="primary">
              Open judge walkthrough <ArrowRight size={16} />
            </Button>
            <Button href="/evidence" variant="secondary">
              Review evidence map
            </Button>
          </div>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}
