import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BriefcaseBusiness,
  Building2,
  Check,
  ClipboardCheck,
  Cpu,
  Fingerprint,
  GitBranch,
  Layers3,
  Lock,
  Scale,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { MarketingFooter } from "./marketing-footer";
import { MarketingGovernance } from "./marketing-governance";
import { MarketingNav } from "./marketing-nav";
import { MarketingWorkflow } from "./marketing-workflow";
import {
  MarketingPathways,
  MarketingProductPreview,
} from "./marketing-product-preview";
import { DemoNotice } from "./demo-boundary";
import { Stagger } from "./motion";
import { Button, Card, SectionHeader, StatusBadge } from "./ui";

const solutionSteps = [
  [
    "01",
    "Prepare",
    "Practice briefs, feedback, and evidence build the foundation before a student sees paid work.",
  ],
  [
    "02",
    "Assess",
    "Readiness is grounded in work evidence and human review, not a popularity score.",
  ],
  [
    "03",
    "Match",
    "Complete briefs and transparent terms help qualified students decide whether work fits.",
  ],
  [
    "04",
    "Deliver",
    "Project squads work inside an agreed scope with technical supervision and milestone review.",
  ],
  [
    "05",
    "Verify",
    "QA findings, acceptance, consent, and payment records form a durable project record.",
  ],
  [
    "06",
    "Pay",
    "Compensation is visible before acceptance and released through accountable operational controls.",
  ],
];

const categories = [
  [
    "AI workflow automation",
    "Reduce repetitive internal work with bounded, reviewable automations.",
    "Process map · integration plan · tested handoff",
    GitBranch,
  ],
  [
    "Data dashboards & reporting",
    "Turn recurring operational questions into clear, maintainable views.",
    "Data contract · dashboard · interpretation guide",
    BarChart3,
  ],
  [
    "Internal business tools",
    "Give teams a focused interface for a real workflow, record, or decision.",
    "Responsive UI · role boundaries · release evidence",
    Layers3,
  ],
  [
    "Customer & operations portals",
    "Make a narrow customer or service journey easier to complete and support.",
    "Journey map · accessible surface · acceptance checklist",
    Building2,
  ],
];

export function LandingPage() {
  return (
    <main id="main-content" className="marketing-site">
      <MarketingNav />
      <section className="marketing-hero">
        <div className="marketing-container marketing-hero-grid">
          <div className="marketing-hero-copy">
            <p className="marketing-eyebrow">
              The AI-operated apprenticeship studio
            </p>
            <h1>
              Turn potential into paid professional experience—with proof.
            </h1>
            <p className="marketing-lead">
              PraxisAI prepares emerging technical talent, deploys supervised
              teams to bounded company projects, and records the evidence that
              connects learning to trusted delivery.
            </p>

            {/* XPRIZE Judge Quick Sandbox Callout */}
            <div className="judge-hero-banner">
              <div className="judge-hero-banner-info">
                <span className="judge-hero-banner-badge">
                  <Sparkles size={13} aria-hidden="true" /> XPRIZE
                </span>
                <span className="judge-hero-banner-title">
                  Evaluation Sandbox: Test live multi-agent operations &
                  economics
                </span>
              </div>
              <div className="judge-hero-banner-actions">
                <Button href="/judge" variant="primary">
                  14-Step Walkthrough{" "}
                  <ArrowRight size={14} aria-hidden="true" />
                </Button>
                <Button href="/business-model" variant="outline">
                  Unit Economics
                </Button>
              </div>
            </div>

            <div className="marketing-actions">
              <Button href="/contact" variant="primary">
                Submit a company project{" "}
                <ArrowRight size={17} aria-hidden="true" />
              </Button>
              <Button href="/for-students" variant="secondary">
                Apply for the apprenticeship
              </Button>
              <Button href="/judge" variant="link">
                See the 3-minute judge walkthrough{" "}
                <ArrowRight size={15} aria-hidden="true" />
              </Button>
            </div>
            <p className="marketing-trust-note">
              <ShieldCheck size={17} aria-hidden="true" /> Transparent pay{" "}
              <span>·</span> Human supervision <span>·</span> Verified project
              evidence
            </p>
            <DemoNotice className="hero-demo-notice">
              Public product previews use sanitized demo data, not customer
              traction.
            </DemoNotice>
          </div>
          <MarketingWorkflow />
        </div>
      </section>

      <div className="marketing-ribbon">
        <div className="marketing-container">
          <span>
            Students build proof. Employers choose. Teams verify delivery.
          </span>
          <Fingerprint size={24} aria-hidden="true" />
        </div>
      </div>

      <section
        className="marketing-metrics-bar"
        aria-label="Core platform operational guarantees"
      >
        <div className="marketing-container marketing-metrics-grid">
          <div className="marketing-metric-item">
            <div className="marketing-metric-icon">
              <Lock size={19} aria-hidden="true" />
            </div>
            <div>
              <strong>Deterministic Safety</strong>
              <span>State machine invariants with human-only gates</span>
            </div>
          </div>
          <div className="marketing-metric-item">
            <div className="marketing-metric-icon">
              <ShieldCheck size={19} aria-hidden="true" />
            </div>
            <div>
              <strong>W3C Verifiable Proof</strong>
              <span>Cryptographically signed tamper-evident ledger</span>
            </div>
          </div>
          <div className="marketing-metric-item">
            <div className="marketing-metric-icon">
              <Cpu size={19} aria-hidden="true" />
            </div>
            <div>
              <strong>Dual Gemini Telemetry</strong>
              <span>Vertex AI & AI Studio token/latency tracking</span>
            </div>
          </div>
          <div className="marketing-metric-item">
            <div className="marketing-metric-icon">
              <Scale size={19} aria-hidden="true" />
            </div>
            <div>
              <strong>Escrow Ledger</strong>
              <span>Reconciled accounting with zero hidden deductions</span>
            </div>
          </div>
        </div>
      </section>

      <section className="marketing-section marketing-section-muted">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="Why this model exists"
            title="Opportunity should not depend on already having opportunity."
            description="Students need real practice and evidence before companies can trust them with consequential work. Companies need a bounded delivery partner for digital work that does not justify a full internal team. PraxisAI connects those needs with clear human accountability."
          />
          <Stagger className="problem-grid">
            <Card>
              <span className="problem-number">01</span>
              <h3>
                Students are asked to prove experience before they can get it.
              </h3>
              <p>
                Practice work becomes more valuable when it teaches the same
                scoping, communication, testing, and handoff habits that real
                projects require.
              </p>
            </Card>
            <Card>
              <span className="problem-number">02</span>
              <h3>
                Companies have useful work that falls between a task and a full
                hire.
              </h3>
              <p>
                Small automation, data, and internal-tool projects still need a
                clear brief, reliable execution, and someone accountable for
                review.
              </p>
            </Card>
            <Card>
              <span className="problem-number">03</span>
              <h3>Traditional pathways leave the proof scattered.</h3>
              <p>
                Learning records, supervisor feedback, project acceptance, and
                compensation evidence should connect into a record a person can
                actually use.
              </p>
            </Card>
          </Stagger>
        </div>
      </section>

      <section className="marketing-section">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="One connected system"
            title="Prepare. Assess. Match. Deliver. Verify. Pay."
            description="Each stage has a different kind of evidence and a different authority boundary. That separation keeps the experience useful without pretending AI can replace accountable decisions."
          />
          <Stagger className="solution-grid">
            {solutionSteps.map(([number, title, detail]) => (
              <article className="solution-step" key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{detail}</p>
              </article>
            ))}
          </Stagger>
        </div>
      </section>

      <section className="marketing-section marketing-section-dark">
        <div className="marketing-container audience-grid">
          <div>
            <p className="marketing-eyebrow">For people building a career</p>
            <h2>Professional growth with visible terms.</h2>
            <p>
              Students can learn through practical assignments, understand what
              readiness means, review complete paid offers, and build a
              consent-based portfolio of work.
            </p>
            <ul className="check-list">
              <li>
                <Check size={17} aria-hidden="true" /> No payment to access
                assignments.
              </li>
              <li>
                <Check size={17} aria-hidden="true" /> No reputation penalty for
                declining an offer.
              </li>
              <li>
                <Check size={17} aria-hidden="true" /> Human supervision and
                appeal routes.
              </li>
              <li>
                <Check size={17} aria-hidden="true" /> Verifiable credentials
                when evidence supports them.
              </li>
            </ul>
            <Button href="/for-students" variant="light">
              Explore the student journey{" "}
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
          <div className="audience-panel">
            <p className="marketing-eyebrow">For companies</p>
            <h2>One accountable path from brief to release.</h2>
            <p>
              Bring a bounded digital project. PraxisAI helps structure the
              scope, match qualified contributors, coordinate supervision, and
              keep milestone evidence visible.
            </p>
            <div className="audience-panel-meta">
              <span>
                <BriefcaseBusiness size={17} aria-hidden="true" /> Managed
                delivery
              </span>
              <span>
                <ClipboardCheck size={17} aria-hidden="true" /> Reviewable
                evidence
              </span>
              <span>
                <Users size={17} aria-hidden="true" /> Supervised teams
              </span>
            </div>
            <Button href="/for-companies" variant="outline-light">
              See the company experience{" "}
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      </section>

      <MarketingProductPreview />
      <MarketingPathways />

      <section className="marketing-section">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="AI with boundaries"
            title="AI can accelerate the operation without owning the outcome."
            description="PraxisAI uses Gemini agents to assist with structured, low-risk work. Deterministic services control money, permissions, and project state. Humans approve consequential decisions."
          />
          <div className="authority-grid">
            <Card>
              <StatusBadge tone="ai">AI may propose</StatusBadge>
              <h3>Scope, plans, matches, summaries, and QA findings</h3>
              <p>
                Agents return structured proposals with evidence references and
                confidence signals for review.
              </p>
            </Card>
            <Card>
              <StatusBadge tone="success">Low-risk automation</StatusBadge>
              <h3>Approved operational tasks</h3>
              <p>
                Only explicitly permitted, reversible actions can run
                automatically inside the configured policy boundary.
              </p>
            </Card>
            <Card>
              <StatusBadge tone="warning">Human approval</StatusBadge>
              <h3>Money, access, release, disputes, and credentials</h3>
              <p>
                People retain authority over decisions that affect rights,
                payment, reputation, or public claims.
              </p>
            </Card>
            <Card>
              <StatusBadge>Deterministic system</StatusBadge>
              <h3>State, permissions, and append-only records</h3>
              <p>
                Business rules and audit records do not depend on a model
                deciding what happened.
              </p>
            </Card>
          </div>
          <div className="authority-note">
            <Sparkles size={18} aria-hidden="true" />
            <span>
              No private model reasoning is exposed. The product shows
              structured rationale, evidence, policy decisions, and human
              approvals.
            </span>
          </div>
          <MarketingGovernance />
        </div>
      </section>

      <section className="marketing-section marketing-section-muted">
        <div className="marketing-container">
          <SectionHeader
            eyebrow="Project boundaries"
            title="Useful work, scoped for supervision."
            description="The initial studio focuses on projects that can be explained clearly, delivered in a bounded timeframe, and reviewed by a qualified human."
          />
          <div className="category-grid">
            {categories.map(([title, detail, deliverables, Icon]) => {
              const CategoryIcon = Icon;
              return (
                <Card key={title as string}>
                  <CategoryIcon size={22} aria-hidden="true" />
                  <h3>{title as string}</h3>
                  <p>{detail as string}</p>
                  <span className="category-deliverables">
                    {deliverables as string}
                  </span>
                  <Button href="/solutions" variant="link">
                    Explore the fit <ArrowRight size={15} aria-hidden="true" />
                  </Button>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      <section className="marketing-section">
        <div className="marketing-container evidence-grid">
          <div>
            <SectionHeader
              eyebrow="Trust and evidence"
              title="The record matters as much as the result."
              description="PraxisAI is designed so participants and clients can understand how a decision was made, what was reviewed, and what remains unverified."
            />
            <Button href="/trust" variant="secondary">
              Read the trust model <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
          <div className="evidence-list">
            <div>
              <ShieldCheck size={20} aria-hidden="true" />
              <span>
                <strong>Visible compensation</strong>
                <small>
                  Pay, hours, scope, and revisions are part of the offer.
                </small>
              </span>
            </div>
            <div>
              <ClipboardCheck size={20} aria-hidden="true" />
              <span>
                <strong>Acceptance evidence</strong>
                <small>
                  QA findings and client decisions remain distinct records.
                </small>
              </span>
            </div>
            <div>
              <Fingerprint size={20} aria-hidden="true" />
              <span>
                <strong>Consent-based proof</strong>
                <small>
                  Portfolio sharing and credentials respect participant control.
                </small>
              </span>
            </div>
            <div>
              <BadgeCheck size={20} aria-hidden="true" />
              <span>
                <strong>Appeals and review</strong>
                <small>
                  Consequential decisions have a human route for
                  reconsideration.
                </small>
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="marketing-section marketing-final-cta">
        <div className="marketing-container">
          <p className="marketing-eyebrow">Start with the right next step</p>
          <h2>Build the proof that makes opportunity possible.</h2>
          <p>
            Whether you have a project to scope or are ready to prepare for one,
            PraxisAI keeps the next action clear.
          </p>
          <div className="marketing-actions">
            <Button href="/contact" variant="primary">
              Start with a project brief{" "}
              <ArrowRight size={17} aria-hidden="true" />
            </Button>
            <Button href="/for-students" variant="secondary">
              Start your application
            </Button>
          </div>
        </div>
      </section>
      <MarketingFooter />
    </main>
  );
}
