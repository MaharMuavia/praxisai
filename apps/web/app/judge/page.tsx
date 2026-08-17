import type { Metadata } from "next";
import { ArrowRight, Award, Check, ShieldCheck, Sparkles } from "lucide-react";
import { DemoNotice } from "@/components/demo-boundary";
import { JudgeSandbox } from "@/features/judge/judge-sandbox";
import { JudgeScorecard } from "@/features/judge/judge-scorecard";
import { JudgeWalkthrough } from "@/features/judge/judge-walkthrough";
import { MarketingFooter } from "@/components/marketing-footer";
import { MarketingNav } from "@/components/marketing-nav";
import { Button, Card } from "@/components/ui";

export const metadata: Metadata = {
  title: "Judge & Evaluator Hub · Gemini XPRIZE",
  description:
    "Interactive deterministic walkthrough of PraxisAI's Gemini agent contract, authority boundaries, and cryptographic evidence.",
};

export default function JudgePage() {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="judge-hero">
        <div className="marketing-container judge-hero-grid">
          <div>
            <p className="marketing-eyebrow">
              XPRIZE Gemini Hackathon Evaluator Hub
            </p>
            <h1>Real-world impact. Zero hallucinated authority.</h1>
            <p className="marketing-lead">
              Walk the Gemini agent contract with deterministic, pre-scripted
              examples: structured scoping and multimodal QA proposals, the
              policy boundary, transparent escrow math, and append-only
              cryptographic audit records.
            </p>
            <div className="marketing-actions">
              <a className="ui-button ui-button-primary" href="#sandbox">
                Open the sandbox <Sparkles size={16} />
              </a>
              <a className="ui-button ui-button-secondary" href="#rubric">
                Criteria alignment <Award size={16} />
              </a>
              <a className="ui-button ui-button-secondary" href="#walkthrough">
                14-Step Lifecycle <ArrowRight size={16} />
              </a>
            </div>
            <DemoNotice>
              Illustrative deterministic scenarios — pre-scripted, not live
              model calls. Real recorded agent runs appear in the operations
              center once the API is deployed with a Gemini provider.
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
                <Check size={16} /> Gemini returns strongly typed Pydantic
                proposals
              </li>
              <li>
                <Check size={16} /> Multimodal QA evaluates screenshots, UI
                layouts & code
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

      {/* SECTION 1: INTERACTIVE SANDBOX */}
      <section
        id="sandbox"
        className="marketing-section judge-section judge-sandbox-section"
      >
        <div className="marketing-container">
          <JudgeSandbox />
        </div>
      </section>

      {/* SECTION 2: XPRIZE RUBRIC & SCORECARD */}
      <section
        id="rubric"
        className="marketing-section marketing-section-muted judge-section"
      >
        <div className="marketing-container">
          <JudgeScorecard />
        </div>
      </section>

      {/* SECTION 3: 14-STEP LIFECYCLE WALKTHROUGH */}
      <section id="walkthrough" className="marketing-section judge-section">
        <div className="marketing-container">
          <JudgeWalkthrough />
        </div>
      </section>

      {/* SECTION 4: EVIDENCE & BUSINESS MODEL */}
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
