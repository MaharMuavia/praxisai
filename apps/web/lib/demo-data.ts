import type { components } from "@praxisai/api-client";
import { demoEnvironment } from "./demo-environment";

type Session = components["schemas"]["SessionView"];
type Project = components["schemas"]["ProjectView"];
type Dashboard = components["schemas"]["DashboardSummary"];
type Notification = components["schemas"]["NotificationView"];
type NotificationPreference =
  components["schemas"]["NotificationPreferenceView"];
type LearningPath = components["schemas"]["LearningPathView"];
type Opportunity = components["schemas"]["OpportunityView"];
type StudentProposal = components["schemas"]["StudentProposalView"];
type EmployerOpportunity = components["schemas"]["EmployerOpportunityView"];

export type DemoTrendPoint = {
  label: string;
  value: number;
};

export type DemoActivity = {
  id: string;
  title: string;
  detail: string;
  time: string;
  tone: "cyan" | "lime" | "violet" | "amber";
};

export type DemoWorkspaceSnapshot = {
  session: Session;
  projects: Project[];
  dashboard: Dashboard;
  notifications: Notification[];
  notificationPreferences: NotificationPreference[];
  learningPaths: LearningPath[];
  opportunities: Opportunity[];
  proposals: StudentProposal[];
  employerOpportunities: EmployerOpportunity[];
  trends: {
    studentReadiness: DemoTrendPoint[];
    clientDelivery: DemoTrendPoint[];
    operationsFlow: DemoTrendPoint[];
    universityOutcomes: DemoTrendPoint[];
  };
  activity: DemoActivity[];
};

const ids = {
  student: "11111111-1111-4111-8111-111111111111",
  client: "22222222-2222-4222-8222-222222222222",
  projectActive: "33333333-3333-4333-8333-333333333333",
  projectCompleted: "44444444-4444-4444-8444-444444444444",
  projectWaiting: "55555555-5555-4555-8555-555555555555",
  opportunityOne: "66666666-6666-4666-8666-666666666666",
  opportunityTwo: "77777777-7777-4777-8777-777777777777",
  path: "88888888-8888-4888-8888-888888888888",
  proposal: "99999999-9999-4999-8999-999999999999",
};

const now = "2026-08-01T08:00:00.000Z";

const demoSession: Session = {
  user_id: ids.student,
  display_name: "Amina Noor",
  email: "amina@student.demo",
  active_membership: {
    organization_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    organization_name: "PraxisAI Pilot Operations",
    role: "student",
  },
  capabilities: ["learning:read", "opportunities:read", "proposals:create"],
  onboarding_state: "COMPLETE",
  notification_count: 2,
  environment_label: "demo",
  required_consent_versions: {},
};

const demoProjects: Project[] = [
  {
    id: ids.projectActive,
    client_organization_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    title: "Northstar resource directory",
    description:
      "A supervised accessibility-first directory for a fictional civic studio.",
    category: "website",
    state: "ACTIVE",
    version: 7,
    required_deposit_minor: 180000,
    funded_minor: 180000,
    currency: "USD",
    complexity: "LOW",
    is_demo: true,
    created_at: "2026-07-18T10:00:00.000Z",
  },
  {
    id: ids.projectCompleted,
    client_organization_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    title: "Accessible resource directory",
    description:
      "Completed fictional directory project with verified evidence.",
    category: "website",
    state: "COMPLETED",
    version: 18,
    required_deposit_minor: 180000,
    funded_minor: 180000,
    currency: "USD",
    complexity: "LOW",
    is_demo: true,
    created_at: "2025-12-08T10:00:00.000Z",
  },
  {
    id: ids.projectWaiting,
    client_organization_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    title: "Volunteer onboarding workflow",
    description:
      "A fictional intake and review workflow for a volunteer group.",
    category: "workflow_automation",
    state: "AWAITING_STUDENT_ACCEPTANCE",
    version: 7,
    required_deposit_minor: 240000,
    funded_minor: 240000,
    currency: "USD",
    complexity: "LOW",
    is_demo: true,
    created_at: "2026-07-24T10:00:00.000Z",
  },
];

const demoLearningPaths: LearningPath[] = [
  {
    id: ids.path,
    slug: "frontend-delivery",
    title: "Frontend delivery foundations",
    summary:
      "Build accessible, tested interfaces and learn to explain the evidence behind each release.",
    level: "FOUNDATION",
    estimated_hours: 18,
    progress_percent: 58,
    enrolled: true,
    status: "IN_PROGRESS",
    prerequisites: ["HTML and CSS basics"],
    skill_outcomes: ["Accessible UI", "Component thinking", "Release evidence"],
    modules: [
      {
        id: "module-1-1111-4111-8111-111111111111",
        ordinal: 1,
        title: "Read the brief",
        summary: "Turn an ambiguous request into visible acceptance criteria.",
        estimated_minutes: 35,
        completed: true,
        completion_evidence: "Brief summary and acceptance checklist",
        exercise_brief:
          "Rewrite a civic directory request as a testable brief.",
        content_sections: [
          {
            title: "Start with outcomes",
            body: "Name who needs the change and what success looks like.",
          },
        ],
      },
      {
        id: "module-2-2222-4222-8222-222222222222",
        ordinal: 2,
        title: "Build an accessible surface",
        summary: "Use semantic structure, keyboard paths, and useful states.",
        estimated_minutes: 55,
        completed: true,
        completion_evidence: "Annotated component and accessibility notes",
        exercise_brief:
          "Create an empty-state and filterable directory surface.",
        content_sections: [
          {
            title: "Design the states",
            body: "Loading, empty, error, and success states are part of the feature.",
          },
        ],
      },
      {
        id: "module-3-3333-4333-8333-333333333333",
        ordinal: 3,
        title: "Prove the release",
        summary:
          "Connect tests, screenshots, and decisions into useful evidence.",
        estimated_minutes: 65,
        completed: false,
        completion_evidence: "Test output, screenshot, and short release note",
        exercise_brief:
          "Package a review-ready release note for the directory.",
        content_sections: [
          {
            title: "Evidence is the handoff",
            body: "A reviewer should be able to understand what changed and why.",
          },
        ],
      },
    ],
  },
  {
    id: "path-automation-4444-4444-8444-444444444444",
    slug: "workflow-automation",
    title: "Workflow automation starter",
    summary: "Map dependable workflows before introducing automation.",
    level: "EXPLORER",
    estimated_hours: 12,
    progress_percent: 0,
    enrolled: false,
    status: null,
    prerequisites: ["Basic spreadsheets"],
    skill_outcomes: ["Process mapping", "Validation", "Human handoffs"],
    modules: [],
  },
];

const demoProposals: StudentProposal[] = [
  {
    id: ids.proposal,
    opportunity_id: ids.opportunityOne,
    student_user_id: ids.student,
    student_display_name: "Amina Noor",
    state: "SUBMITTED",
    cover_note:
      "I can turn the current directory brief into a clear, keyboard-friendly release.",
    approach:
      "I would start with the role and transition matrix, then build the API contract and accessible states.",
    delivery_plan: [
      {
        milestone: "Brief and route map",
        outcome: "Approved structure and testable acceptance criteria",
      },
      {
        milestone: "Directory surface",
        outcome: "Responsive, filterable UI with documented states",
      },
      {
        milestone: "Release evidence",
        outcome: "Tests, keyboard review, and handoff note",
      },
    ],
    relevant_evidence: [
      {
        title: "Community directory practice",
        url: "https://example.invalid/praxisai/directory",
        relevance: "Shows accessible filtering and empty-state decisions.",
      },
    ],
    proposed_amount_minor: 135000,
    currency: "USD",
    estimated_days: 8,
    availability_hours_per_week: 12,
    created_at: "2026-07-29T09:00:00.000Z",
    decided_at: null,
    decision_reason: null,
  },
];

const demoOpportunities: Opportunity[] = [
  {
    id: ids.opportunityOne,
    project_id: ids.projectActive,
    employer_name: "Northstar Civic Studio",
    headline: "Make a civic resource directory easier to use",
    brief:
      "Create a small, accessible directory experience that helps residents find the right resource without guesswork.",
    budget_minor: 180000,
    currency: "USD",
    estimated_hours_low: 14,
    estimated_hours_high: 20,
    deadline: "2026-08-28T17:00:00.000Z",
    supervision_level: "guided",
    status: "OPEN",
    created_at: "2026-07-21T10:00:00.000Z",
    required_skills: ["React", "Accessibility", "Testing"],
    nice_to_have_skills: ["Content design"],
    deliverables: [
      "Responsive directory UI",
      "Keyboard review notes",
      "Release handoff",
    ],
    proposal_requirements: ["Approach", "Milestone plan", "Relevant evidence"],
    proposal_count: 4,
    my_proposal: demoProposals[0],
  },
  {
    id: ids.opportunityTwo,
    project_id: ids.projectWaiting,
    employer_name: "Brightpath Volunteer Network",
    headline: "Clarify volunteer onboarding steps",
    brief:
      "Turn a manual intake checklist into a calm, reviewable onboarding workflow.",
    budget_minor: 150000,
    currency: "USD",
    estimated_hours_low: 12,
    estimated_hours_high: 18,
    deadline: "2026-09-12T17:00:00.000Z",
    supervision_level: "supported",
    status: "OPEN",
    created_at: "2026-07-25T10:00:00.000Z",
    required_skills: ["Workflow mapping", "Forms", "Validation"],
    nice_to_have_skills: ["Automation"],
    deliverables: ["Onboarding flow", "Validation checklist", "Operator guide"],
    proposal_requirements: ["Workflow approach", "Evidence of practice"],
    proposal_count: 2,
    my_proposal: null,
  },
];

const demoEmployerOpportunities: EmployerOpportunity[] = demoOpportunities.map(
  (opportunity) => ({
    ...opportunity,
    proposals: opportunity.id === ids.opportunityOne ? demoProposals : [],
  }),
);

export const demoWorkspaceSnapshot: DemoWorkspaceSnapshot = {
  session: demoSession,
  projects: demoProjects,
  dashboard: {
    pending_approvals: 7,
    failed_agent_runs: 2,
    dead_letter_jobs: 1,
    payment_exceptions: 1,
    environment_label: "demo",
    is_demo: true,
    projects_by_state: {
      ACTIVE: 4,
      COMPLETED: 9,
      AWAITING_CLIENT_DECISION: 2,
      AWAITING_STUDENT_ACCEPTANCE: 3,
    },
  },
  notifications: [
    {
      id: "notification-1111-4111-8111-111111111111",
      kind: "projects",
      title: "Scope decision requested",
      body: "Northstar Civic Studio has a fictional demo project ready for review.",
      resource_path: "/client/projects",
      read_at: null,
      created_at: now,
    },
    {
      id: "notification-2222-4222-8222-222222222222",
      kind: "credentials",
      title: "Credential evidence reminder",
      body: "Review the evidence attached to your completed demo project.",
      resource_path: "/student/credentials",
      read_at: null,
      created_at: "2026-07-31T08:00:00.000Z",
    },
    {
      id: "notification-3333-4333-8333-333333333333",
      kind: "operations",
      title: "Cohort report available",
      body: "Privacy-safe fictional cohort metrics are ready to inspect.",
      resource_path: "/university",
      read_at: "2026-07-30T08:00:00.000Z",
      created_at: "2026-07-30T08:00:00.000Z",
    },
  ],
  notificationPreferences: [
    { category: "projects", enabled: true },
    { category: "payments", enabled: true },
    { category: "credentials", enabled: true },
    { category: "operations", enabled: false },
  ],
  learningPaths: demoLearningPaths,
  opportunities: demoOpportunities,
  proposals: demoProposals,
  employerOpportunities: demoEmployerOpportunities,
  trends: {
    studentReadiness: [
      { label: "W1", value: 24 },
      { label: "W2", value: 31 },
      { label: "W3", value: 39 },
      { label: "W4", value: 44 },
      { label: "W5", value: 51 },
      { label: "W6", value: 58 },
    ],
    clientDelivery: [
      { label: "Mar", value: 5 },
      { label: "Apr", value: 7 },
      { label: "May", value: 6 },
      { label: "Jun", value: 9 },
      { label: "Jul", value: 12 },
      { label: "Aug", value: 14 },
    ],
    operationsFlow: [
      { label: "Mon", value: 18 },
      { label: "Tue", value: 23 },
      { label: "Wed", value: 19 },
      { label: "Thu", value: 27 },
      { label: "Fri", value: 31 },
      { label: "Sat", value: 28 },
    ],
    universityOutcomes: [
      { label: "Q1", value: 42 },
      { label: "Q2", value: 55 },
      { label: "Q3", value: 63 },
      { label: "Q4", value: 78 },
    ],
  },
  activity: [
    {
      id: "activity-1",
      title: "Practice evidence recorded",
      detail: "Accessible UI module",
      time: "12m ago",
      tone: "cyan",
    },
    {
      id: "activity-2",
      title: "Proposal opened",
      detail: "Northstar resource directory",
      time: "2h ago",
      tone: "lime",
    },
    {
      id: "activity-3",
      title: "Lead review completed",
      detail: "Release evidence passed",
      time: "Yesterday",
      tone: "violet",
    },
    {
      id: "activity-4",
      title: "Funding evidence verified",
      detail: "Volunteer onboarding workflow",
      time: "2d ago",
      tone: "amber",
    },
  ],
};

export function isRecoverableDemoError(reason: unknown): boolean {
  if (reason instanceof TypeError) return true;
  if (!(reason instanceof Error)) return false;
  return /failed to fetch|networkerror|request failed \((?:5\d\d)\)/i.test(
    reason.message,
  );
}

export async function withDemoFallback<T>(
  request: Promise<T>,
  fallback: T,
): Promise<{ data: T; isDemo: boolean }> {
  try {
    return { data: await request, isDemo: false };
  } catch (reason: unknown) {
    if (!demoEnvironment.allowDemoFallback || !isRecoverableDemoError(reason))
      throw reason;
    return { data: fallback, isDemo: true };
  }
}
