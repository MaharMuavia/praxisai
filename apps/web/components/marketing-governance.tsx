import {
  ArrowRight,
  Check,
  Fingerprint,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { Reveal } from "./motion";

const states = [
  [
    "01",
    "AI proposes",
    "Gemini scope draft",
    "Structured rationale and confidence",
  ],
  [
    "02",
    "Policy checks",
    "Permission boundary",
    "No money, access, or release authority",
  ],
  [
    "03",
    "Low-risk action",
    "Draft saved for review",
    "Reversible action with an audit event",
  ],
  [
    "04",
    "Human approval",
    "Coordinator decision",
    "Accountable release or rejection",
  ],
] as const;

export function MarketingGovernance() {
  return (
    <Reveal className="governance-panel">
      <div className="governance-request">
        <span>
          <Fingerprint size={16} aria-hidden="true" /> Request
        </span>
        <strong>
          Project brief → scope draft → policy review → coordinator approval
        </strong>
      </div>
      <div className="governance-grid">
        {states.map(([number, title, value, detail], index) => (
          <div className="governance-state" key={title}>
            <div className="governance-state-top">
              <span>{number}</span>
              {index < states.length - 1 ? (
                <ArrowRight size={15} aria-hidden="true" />
              ) : (
                <Check size={15} aria-hidden="true" />
              )}
            </div>
            <strong>{title}</strong>
            <span className="governance-value">{value}</span>
            <small>{detail}</small>
          </div>
        ))}
      </div>
      <div className="governance-footer">
        <span>
          <ShieldCheck size={15} aria-hidden="true" /> Structured rationale only
        </span>
        <span>
          <UserRound size={15} aria-hidden="true" /> Human authority retained
        </span>
      </div>
    </Reveal>
  );
}
