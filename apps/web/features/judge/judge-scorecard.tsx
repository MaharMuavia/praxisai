"use client";

import {
  Award,
  Cpu,
  Globe2,
  Sparkles,
  ThumbsUp,
  TriangleAlert,
} from "lucide-react";
import { Card } from "@/components/ui";

type CriterionCard = {
  criterion: string;
  weight: string;
  icon: typeof Sparkles;
  strengths: string[];
  gaps: string[];
  evidence: string;
};

// Maps to the three equally weighted Build with Gemini judging criteria.
// This is an honest self-assessment — strengths AND gaps — not a self-assigned
// score. Judges assign scores; we point to where each claim can be checked.
const CRITERIA: CriterionCard[] = [
  {
    criterion: "AI-Native Operations",
    weight: "1 of 3 equal criteria",
    icon: Sparkles,
    strengths: [
      "Four Gemini workflows on the google-genai SDK with enforced response_schema — malformed output fails closed rather than entering the database.",
      "Native multimodal QA: screenshots, PDFs, and diagrams passed via Part.from_bytes against a rubric.",
      "Versioned, centralized prompts that treat every brief as untrusted data; bounded retries with backoff and a 30s timeout.",
      "Every run recorded in an append-only agent_runs table: model, prompt version, latency, tokens, retries, correlation ID.",
    ],
    gaps: [
      "Not yet deployed — zero production Gemini traffic has been served, so no live usage records exist.",
      "Agents propose only. Every run sets human_approval_required and empty executed_action_evidence; no decision is committed autonomously yet.",
    ],
    evidence:
      "apps/api/app/agents/provider.py · prompts.py · apps/api/app/domain/models.py (agent_runs)",
  },
  {
    criterion: "Business Viability",
    weight: "1 of 3 equal criteria",
    icon: Globe2,
    strengths: [
      "Coherent model: bounded projects, escrow ledger, and a 70/30 split enforced in code as a product invariant.",
      "Narrow, defensible wedge (AI automation, dashboards, internal tools) that keeps supervised junior delivery safe.",
      "Unit economics are internally consistent and documented in docs/pilot-pipeline.md.",
    ],
    gaps: [
      "Pre-revenue: $0 in the competition window (docs/xprize-pnl-statement.md). No users, no signed partners.",
      "No payment processor integrated — PAYMENT_PROVIDER is manual_external; funds cannot be collected or settled in-product.",
      "Commercial validation (distribution, willingness to pay, delivery capacity) is not started.",
    ],
    evidence:
      "docs/xprize-pnl-statement.md · docs/pilot-pipeline.md · apps/api/app/domain/pricing.py",
  },
  {
    criterion: "Category Impact",
    weight: "1 of 3 equal criteria",
    icon: Award,
    strengths: [
      "Targets the learning-to-earning gap by binding preparation to paid, supervised delivery.",
      "Cryptographic proof of work: W3C Verifiable Credentials with signature and append-only revocation checked at verification.",
      "A safety pattern for AI in education — bounded agent authority with a deterministic policy engine and human release gates.",
    ],
    gaps: [
      "Impact is demonstrated by architecture and tests, not yet by outcomes — no student has completed a paid project.",
      "Adoption path depends on the deployment and commercial steps above.",
    ],
    evidence:
      "apps/api/app/credentials/ · apps/api/app/domain/policies.py · apps/web/features/internships/",
  },
];

export function JudgeScorecard() {
  return (
    <div className="judge-scorecard" id="judge-scorecard">
      <div className="judge-scorecard-header">
        <div>
          <span className="marketing-eyebrow">Criteria alignment</span>
          <h2>How PraxisAI maps to the three judging criteria.</h2>
          <p className="marketing-section-description">
            An honest self-assessment against the equally weighted Build with
            Gemini criteria — what is genuinely built and where the real gaps
            are. Scores are the judges&apos; to assign; every claim below points
            to where it can be checked.
          </p>
        </div>
        <div className="scorecard-total-badge">
          <Cpu size={20} />
          <span>230 tests pass locally · CI repair in progress</span>
        </div>
      </div>

      <div className="judge-rubric-grid">
        {CRITERIA.map((item) => {
          const Icon = item.icon;
          return (
            <Card className="judge-rubric-card" key={item.criterion}>
              <div className="rubric-card-top">
                <div className="rubric-card-title-group">
                  <span className="rubric-icon-wrap">
                    <Icon size={18} />
                  </span>
                  <div>
                    <h3>{item.criterion}</h3>
                    <small>{item.weight}</small>
                  </div>
                </div>
              </div>

              <ul className="rubric-criteria-list">
                {item.strengths.map((c, i) => (
                  <li key={`s-${i}`}>
                    <ThumbsUp size={15} className="rubric-check" />
                    <span>{c}</span>
                  </li>
                ))}
                {item.gaps.map((c, i) => (
                  <li key={`g-${i}`}>
                    <TriangleAlert size={15} className="rubric-gap" />
                    <span>
                      <strong>Gap:</strong> {c}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="rubric-evidence-footer">
                <div>
                  <span className="rubric-footer-label">
                    Where to check this
                  </span>
                  <code>{item.evidence}</code>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
