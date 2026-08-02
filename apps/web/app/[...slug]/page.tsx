import { AppShell } from "@/components/app-shell";
import { ContentPage } from "@/components/content-page";
import type { Metadata } from "next";

const publicPages: Record<
  string,
  { title: string; eyebrow: string; description: string; points: string[] }
> = {
  "how-it-works": {
    title: "A practical path from potential to professional proof.",
    eyebrow: "How it works",
    description:
      "PraxisAI connects preparation, assessment, paid project matching, supervised delivery, verification, and compensation in one accountable operating model.",
    points: [
      "Students learn through practical briefs, feedback, and evidence before they are matched to paid work.",
      "Companies bring bounded digital projects with an outcome, constraints, acceptance criteria, and a responsible decision-maker.",
      "AI assists with scope, planning, matching, summaries, and QA findings; humans approve consequential decisions.",
      "Project evidence, client acceptance, compensation, and consent controls remain connected after delivery.",
    ],
  },
  "for-students": {
    title: "Build the proof that makes opportunity possible.",
    eyebrow: "For students",
    description:
      "Learn practical technical habits, show what you can do, and review paid project offers with visible terms and human support.",
    points: [
      "Practice briefs develop scoping, implementation, testing, communication, and handoff skills.",
      "Readiness is grounded in evidence and review rather than proposal volume or a public popularity score.",
      "Offers show scope, role, hours, pay, timing, supervision, revisions, and portfolio rules before you decide.",
      "Declining an offer does not create a reputation penalty, and consequential decisions have an appeal route.",
    ],
  },
  "for-companies": {
    title: "A managed path from business need to accepted release.",
    eyebrow: "For companies",
    description:
      "Bring a bounded AI, data, software, or operations project and get the structure, supervision, and evidence needed to review the work responsibly.",
    points: [
      "Start with an outcome, constraints, acceptance criteria, client participation, and a realistic delivery boundary.",
      "Review transparent project terms and contributor proposals before any work begins.",
      "Use qualified expert leads, milestone visibility, QA findings, and controlled revisions to manage delivery.",
      "Keep funding, acceptance, change orders, and release decisions auditable in one accountable workspace.",
    ],
  },
  "for-expert-leads": {
    title: "Make supervision a structured professional role.",
    eyebrow: "For expert leads",
    description:
      "Expert leads provide the judgment that turns promising work into reviewable delivery without carrying every operational task themselves.",
    points: [
      "Review plans, risks, technical evidence, and deliverables against the agreed scope.",
      "Give students useful feedback and make recommendations that remain distinct from coordinator and client decisions.",
      "Declare conflicts, document review evidence, and escalate issues through a clear support path.",
      "Compensation, review history, and responsibilities are visible rather than informal or assumed.",
    ],
  },
  "for-universities": {
    title: "Privacy-safe evidence of practical participation.",
    eyebrow: "For universities",
    description:
      "Institutions can use consented, purpose-limited reporting to understand participation, learning progress, verified completion, and skills evidence.",
    points: [
      "Cohort reporting suppresses groups below the configured privacy threshold.",
      "Individual earnings, private client information, private feedback, and unconsented evidence remain unavailable.",
      "Exports state their purpose, are audited, and follow the active institutional agreement.",
      "No academic-credit or partnership claim is made without a real agreement and configured consent.",
    ],
  },
  solutions: {
    title: "Small digital projects, delivered with discipline.",
    eyebrow: "Solutions",
    description:
      "The initial studio focuses on practical project categories that can be scoped clearly, supervised by qualified people, and verified with evidence.",
    points: [
      "AI workflow automation for bounded, reviewable operational processes.",
      "Data dashboards and reporting with explicit data contracts and interpretation guidance.",
      "Internal business tools with clear roles, states, and acceptance criteria.",
      "Lightweight customer and operations portals for focused service journeys.",
    ],
  },
  "solutions/ai-automation": {
    title: "Automate the right workflow, with a human handoff.",
    eyebrow: "Solution · AI automation",
    description:
      "Map a real process, identify low-risk opportunities, and release a tested automation with clear exceptions and ownership.",
    points: [
      "Typical outcomes include process maps, integration plans, approval steps, and documented failure handling.",
      "Automation is bounded by permissions, deterministic rules, and explicit human escalation points.",
      "The client supplies access, decision-makers, and acceptance criteria needed to test the workflow.",
    ],
  },
  "solutions/data-dashboards": {
    title: "Make recurring decisions easier to see.",
    eyebrow: "Solution · Data dashboards",
    description:
      "Turn recurring operational questions into clear views that explain definitions, freshness, limitations, and the next decision.",
    points: [
      "Typical deliverables include a data contract, dashboard surface, text summary, and interpretation guide.",
      "Every metric should have a definition, source, time window, and clear empty or suppressed state.",
      "The client owns source access and validates whether the resulting view supports the intended decision.",
    ],
  },
  "solutions/internal-tools": {
    title: "Focused tools for the work your team actually does.",
    eyebrow: "Solution · Internal tools",
    description:
      "Build a narrow, accessible interface around a real internal workflow, record, or review decision.",
    points: [
      "Start with roles, states, acceptance criteria, and the smallest useful surface.",
      "Responsive layouts, keyboard paths, and useful empty, error, and permission states are part of delivery.",
      "Release evidence connects implementation, testing, review, and handoff into a durable record.",
    ],
  },
  "solutions/customer-portals": {
    title: "A clearer customer or operations journey.",
    eyebrow: "Solution · Customer portals",
    description:
      "Improve a focused service journey with an accessible, supportable portal that makes the next action clear.",
    points: [
      "Typical work includes journey mapping, responsive UI, state handling, and acceptance checklists.",
      "Sensitive information and permissions are explicit rather than implied by the interface.",
      "Clients participate in review and acceptance so the released surface matches the real service need.",
    ],
  },
  "trust/ai-governance": {
    title: "AI assists the operation. It does not hold authority.",
    eyebrow: "Trust · AI governance",
    description:
      "Agents may propose structured work and execute approved low-risk actions; deterministic services and accountable humans control consequential outcomes.",
    points: [
      "Agent runs expose goal, model, input hash, structured output, policy decision, tool results, and correlation ID.",
      "Private model reasoning is not presented as evidence; the product shows structured rationale and source references.",
      "Money, permissions, project state, releases, disputes, and credentials remain outside model authority.",
    ],
  },
  "trust/student-protection": {
    title: "A paid pathway with real boundaries and recourse.",
    eyebrow: "Trust · Student protection",
    description:
      "Students should understand what they are agreeing to, what evidence is collected, how they are paid, and how consequential decisions can be reviewed.",
    points: [
      "No unpaid trial work and no payment to access assignments or the base credential a student earns.",
      "Offers disclose pay, expected hours, deadline, supervision, revisions, and portfolio terms.",
      "No screen, keyboard, camera, or continuous activity monitoring is used as a substitute for work evidence.",
      "Appeals and support routes remain available for QA, payment, credential, and reputation decisions.",
    ],
  },
  "trust/data-and-privacy": {
    title: "Evidence should be useful without becoming surveillance.",
    eyebrow: "Trust · Data and privacy",
    description:
      "PraxisAI is designed around purpose-limited operational evidence, explicit consent, and access boundaries that can be explained.",
    points: [
      "Project and participant evidence is collected for staffing, supervision, payment, verification, or a stated institutional purpose.",
      "Public credentials use a purpose-built verification schema rather than filtered internal records.",
      "Portfolio and university sharing require explicit consent, and retention rules remain operator-configured.",
    ],
  },
  about: {
    title: "A studio built around practice, delivery, and proof.",
    eyebrow: "About PraxisAI",
    description:
      "PraxisAI is building an accountable bridge between emerging technical talent and the real digital work companies need done.",
    points: [
      "The product combines learning, talent matching, project delivery, human supervision, payments evidence, and credentials.",
      "The operating model is deliberately bounded: no unsupported traction claims, no autonomous consequential decisions, and no hidden unpaid work.",
      "The platform is in active development; implementation status is documented rather than presented as a finished promise.",
    ],
  },
  impact: {
    title: "Impact is a record, not a slogan.",
    eyebrow: "Impact",
    description:
      "PraxisAI will report participation, verified completion, compensation, and project evidence only when the underlying records and definitions support the claim.",
    points: [
      "No invented student outcomes, customer counts, revenue, project volume, or AI performance metrics appear on this site.",
      "Future evidence views will identify the definition, source, time window, demo exclusion, and last calculation for each metric.",
      "University reporting and public claims remain subject to consent, privacy suppression, and approval controls.",
    ],
  },
  contact: {
    title: "Start with a clear conversation.",
    eyebrow: "Contact",
    description:
      "Tell us whether you are bringing a project, preparing for paid work, supervising technical delivery, or exploring a university partnership.",
    points: [
      "The public contact form is not yet connected to a production intake endpoint, so this page does not pretend to submit a request.",
      "Companies can use the authenticated project intake once their organization has an active workspace.",
      "Students can review the preparation path and begin through the supported account flow when applications are enabled.",
      "Partnership and expert-lead workflows require an operator-configured intake capability before they can accept records.",
    ],
  },
  "how-it-works/clients": {
    title: "A tighter path from brief to delivery.",
    eyebrow: "For clients",
    description:
      "Submit a constrained project, approve the commercial terms, fund it before work begins, and review only human-approved releases.",
    points: [
      "AI drafts scope and assumptions; a coordinator approves the quote before you see it.",
      "Students choose offers with fixed pay and revision terms; qualified leads supervise complex work.",
      "Deterministic checks, AI findings, lead review, and coordinator release are distinct evidence layers.",
      "Acceptance, approved changes, payments, and project records remain auditable.",
    ],
  },
  "how-it-works/students": {
    title: "Paid work with visible terms and real recourse.",
    eyebrow: "For students",
    description:
      "Matching creates an offer—not an automatic assignment. Participation, earned credentials, appeals, and payout access are free.",
    points: [
      "Review the scope, role, hours, gross pay, deadline, lead, revisions, and portfolio rules before accepting.",
      "Declining or allowing an offer to expire never damages reputation.",
      "Submit milestone evidence without screen, keyboard, camera, or continuous activity monitoring.",
      "Appeal consequential QA, payout, credential, or reputation decisions to a qualified human.",
    ],
  },
  "project-types": {
    title: "Small enough to supervise. Real enough to matter.",
    eyebrow: "Pilot boundaries",
    description:
      "The pilot focuses on 10–40 hour software projects that one qualified technical lead can review.",
    points: [
      "Websites, CRUD tools, dashboards, data analysis, workflow integrations, QA, accessibility, and design systems are supported.",
      "Clinical, financial infrastructure, surveillance, safety-critical, illegal, deceptive, and academic-cheating work is rejected.",
      "Vague startup builds and projects above the effort cap require manual commercial review.",
      "Clients must provide timely access, content, decision-makers, and acceptance criteria.",
    ],
  },
  pricing: {
    title: "The project funds the people doing the work.",
    eyebrow: "Commercial model",
    description:
      "Quotes itemize student compensation, paid technical leadership, the platform service fee, configured taxes, and disclosed provider fees.",
    points: [
      "Examples are illustrative Demo data until an approved rate card is active.",
      "The base agreement includes no more than two ordinary revision rounds.",
      "New deliverables or materially changed criteria require a priced change order and added compensation.",
      "Students never pay to access assignments or receive the base credential they earn.",
    ],
  },
  trust: {
    title: "AI assists the operation. It does not hold authority.",
    eyebrow: "Trust and safeguards",
    description:
      "PraxisAI keeps commercial, technical, financial, dispute, and credential decisions with accountable people and deterministic services.",
    points: [
      "Agents return typed proposals and cannot mutate workflow state.",
      "Private project material and client identity never appear publicly without explicit permission.",
      "Funding and payouts depend on independently verified external evidence and balanced internal records—not browser claims or model output.",
      "Every consequential transition records the actor, reason, prior state, new state, and correlation ID.",
    ],
  },
  universities: {
    title: "Verified outcomes with purpose-limited access.",
    eyebrow: "University pilots",
    description:
      "Institutions can inspect consented project evidence and privacy-safe cohort outcomes under an active agreement.",
    points: [
      "No partnership or academic-credit claim is made without a real institutional agreement.",
      "Minimum cohort sizes suppress identifying aggregate comparisons.",
      "Private client data, individual earnings, coaching notes, and unconsented evidence remain unavailable.",
      "Exports require a stated purpose, are audited, and expire.",
    ],
  },
  terms: {
    title: "Terms of service",
    eyebrow: "Requires legal review",
    description:
      "This demo contains a versioned content placeholder and is not approved legal advice or a production agreement.",
    points: [
      "Project terms will include scope, payment, revisions, intellectual property, disputes, and participant responsibilities.",
      "Jurisdiction-specific language requires qualified legal review before production use.",
    ],
  },
  privacy: {
    title: "Privacy in plain language",
    eyebrow: "Requires legal review",
    description:
      "PraxisAI collects the minimum operational evidence needed to staff, supervise, pay, and verify project work.",
    points: [
      "No screen, keystroke, camera, private-chat, or continuous activity monitoring.",
      "Portfolio and university sharing use explicit, granular consent.",
      "Public credential responses use a purpose-built schema rather than filtered internal records.",
      "Retention, export, deletion, and legal-hold rules require operator and legal configuration.",
    ],
  },
  accessibility: {
    title: "Access is part of delivery quality.",
    eyebrow: "Accessibility",
    description:
      "The product targets WCAG AA contrast, keyboard operation, visible focus, semantic structure, useful errors, and reduced motion.",
    points: [
      "Task boards collapse into navigable lists on small screens.",
      "Known limitations are recorded and prioritized rather than hidden.",
      "Support and escalation paths remain available throughout a project.",
    ],
  },
};

const descriptions: Record<string, string> = {
  client:
    "Projects, decisions, funding, milestones, and released deliverables for the active client organization.",
  student:
    "Offers, supervised delivery work, earnings, appeals, portfolio controls, and verified project credentials.",
  lead: "Compensated supervision, plan reviews, delivery evidence, technical recommendations, and declared conflicts.",
  ops: "Human approval queues, delivery risk, funding exceptions, agent evidence, appeals, payouts, and audit history.",
  admin:
    "Integration status, failed jobs, access controls, retention configuration, and production safety warnings.",
  university:
    "Consented student evidence and privacy-safe cohort outcomes under an active institutional agreement.",
};

const workspacePageMetadata: Record<
  string,
  { title: string; description: string }
> = {
  client: {
    title: "Employer workspace",
    description:
      "Turn business needs into supervised paid projects, compare student evidence, and make accountable hiring decisions.",
  },
  "client/proposals": {
    title: "Student proposals",
    description:
      "Compare each student's approach, delivery plan, evidence, price, and availability before recording a decision.",
  },
  "client/opportunities/new": {
    title: "Publish a paid project",
    description:
      "Give students the business context, deliverables, skills, supervision, budget, and proposal requirements they need.",
  },
  "client/projects/new": {
    title: "Create a project",
    description:
      "Capture the outcome, delivery boundaries, and guardrails used to create the immutable client intake snapshot.",
  },
  student: {
    title: "Career launchpad",
    description:
      "Build practical skills, prove them through project evidence, and compete for transparent paid opportunities.",
  },
  "student/learn": {
    title: "Learn real project skills",
    description:
      "Follow structured paths built around briefs, practice work, feedback, and evidence you can use in proposals.",
  },
  "student/opportunities": {
    title: "Paid project opportunities",
    description:
      "Review complete employer briefs and submit a professional proposal without hidden work or unpaid trials.",
  },
  "student/proposals": {
    title: "My project proposals",
    description:
      "Track every proposal, employer decision, commercial term, and next step from one auditable record.",
  },
};

function titleFrom(path: string) {
  const segment = path.split("/").at(-1) ?? "Overview";
  if (/^[0-9a-f-]{20,}$/i.test(segment)) return "Project command center";
  return segment
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const path = slug.join("/");
  const page = publicPages[path];
  return {
    title: page?.title ?? titleFrom(path),
    description:
      page?.description ??
      "PraxisAI keeps preparation, supervised delivery, and verified project evidence connected.",
  };
}

export default async function CatchAllPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const path = slug.join("/");
  const publicPage = publicPages[path];
  if (publicPage) return <ContentPage {...publicPage} path={path} />;
  const root = slug[0];
  if (
    ["client", "student", "lead", "ops", "admin", "university"].includes(root)
  ) {
    const pageMetadata = workspacePageMetadata[path];
    return (
      <AppShell
        path={`/${path}`}
        title={pageMetadata?.title ?? titleFrom(path)}
        description={
          pageMetadata?.description ??
          descriptions[root] ??
          "Authorized workspace"
        }
      />
    );
  }
  if (["signup", "auth", "invite", "onboarding", "portfolio"].includes(root)) {
    return (
      <ContentPage
        path={path}
        title={titleFrom(path)}
        eyebrow="Account and access"
        description="This flow validates identity, consent, workspace membership, and the permissions required for the requested action."
        points={[
          "Identity and workspace roles are verified by the API.",
          "Invitations and public action tokens expire and are stored as hashes.",
          "Production refuses insecure local authentication.",
          "Recoverable errors preserve entered information without bypassing validation.",
        ]}
      />
    );
  }
  return (
    <ContentPage
      path={path}
      title="Page unavailable"
      eyebrow="Not found"
      description="This route is not part of the active PraxisAI workspace."
      points={[
        "Return to the home page or use an authorized workspace navigation link.",
      ]}
    />
  );
}
