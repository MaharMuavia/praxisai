import type { Metadata } from "next";
import { ArrowRight, Check, ShieldCheck } from "lucide-react";
import { DemoNotice } from "@/components/demo-boundary";
import { JudgeWalkthrough } from "@/features/judge/judge-walkthrough";
import { MarketingFooter } from "@/components/marketing-footer";
import { MarketingNav } from "@/components/marketing-nav";
import { Button, Card } from "@/components/ui";

export const metadata: Metadata = {
  title: "Judge walkthrough",
  description: "A deterministic walkthrough of the PraxisAI operating model.",
};

export default function JudgePage() {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="judge-hero">
        <div className="marketing-container judge-hero-grid">
          <div>
            <p className="marketing-eyebrow">For evaluators and partners</p>
            <h1>See how a real project becomes accountable career proof.</h1>
            <p className="marketing-lead">
              Follow one bounded project from company brief to supervised
              delivery, acceptance, compensation evidence, and consented
              credential proof.
            </p>
            <div className="marketing-actions">
              <a className="ui-button ui-button-primary" href="#walkthrough">
                Start the walkthrough <ArrowRight size={17} />
              </a>
              <Button href="/evidence" variant="secondary">
                Open the evidence map
              </Button>
            </div>
            <DemoNotice>
              Deterministic demo scenario · Fixture AI · Simulated workflow
            </DemoNotice>
          </div>
          <Card className="judge-hero-proof">
            <div className="judge-proof-icon">
              <ShieldCheck size={22} />
            </div>
            <p className="marketing-eyebrow">The authority boundary</p>
            <h2>AI assists. People decide. The system records.</h2>
            <ul>
              <li>
                <Check size={16} /> AI returns structured proposals
              </li>
              <li>
                <Check size={16} /> Humans approve money, access, release, and
                credentials
              </li>
              <li>
                <Check size={16} /> Deterministic services own state and
                append-only evidence
              </li>
            </ul>
          </Card>
        </div>
      </section>
      <section id="walkthrough" className="marketing-section judge-section">
        <div className="marketing-container">
          <JudgeWalkthrough />
        </div>
      </section>
      <section className="marketing-section marketing-section-muted">
        <div className="marketing-container judge-after-grid">
          <div>
            <p className="marketing-eyebrow">Continue the inspection</p>
            <h2>Every claim has a place to be checked.</h2>
            <p className="marketing-section-description">
              Use the evidence map for implementation boundaries, CI
              verification, fixture demonstrations, and items that still require
              an external production check.
            </p>
          </div>
          <div className="marketing-actions">
            <Button href="/evidence" variant="primary">
              View evidence map <ArrowRight size={16} />
            </Button>
            <Button href="/business-model" variant="secondary">
              See the business model
            </Button>
          </div>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}
