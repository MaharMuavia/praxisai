import { AppShell } from "@/components/app-shell";
import { ContentPage } from "@/components/content-page";

const publicPages: Record<
  string,
  { title: string; eyebrow: string; description: string; points: string[] }
> = {
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

export default async function CatchAllPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const path = slug.join("/");
  const publicPage = publicPages[path];
  if (publicPage) return <ContentPage {...publicPage} />;
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
      title="Page unavailable"
      eyebrow="Not found"
      description="This route is not part of the active PraxisAI workspace."
      points={[
        "Return to the home page or use an authorized workspace navigation link.",
      ]}
    />
  );
}
