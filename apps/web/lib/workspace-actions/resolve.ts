import type { WorkspaceActionContext, WorkspacePrimaryAction } from "./types";

function can(context: WorkspaceActionContext, capability: string) {
  return context.session?.capabilities.includes(capability) === true;
}

function projectAction(
  context: WorkspaceActionContext,
  projectId: string,
  state: string,
): WorkspacePrimaryAction | null {
  const href = `/${context.root === "ops" ? "ops" : context.root}/projects/${projectId}`;
  if (
    context.root === "client" &&
    state === "DRAFT" &&
    can(context, "projects:create")
  ) {
    return {
      id: "continue-project-intake",
      label: "Continue project intake",
      href,
      intent: "navigate",
    };
  }
  if (
    context.root === "client" &&
    state === "AWAITING_CLIENT_SCOPE_APPROVAL" &&
    can(context, "projects:approve")
  ) {
    return {
      id: "approve-scope",
      label: "Review scope",
      href,
      capability: "projects:approve",
      intent: "approve",
    };
  }
  if (
    context.root === "client" &&
    state === "AWAITING_DEPOSIT" &&
    can(context, "payments:view")
  ) {
    return {
      id: "fund-project",
      label: "Review funding",
      href,
      capability: "payments:view",
      intent: "review",
    };
  }
  if (
    context.root === "client" &&
    state === "CLIENT_REVIEW" &&
    can(context, "projects:approve")
  ) {
    return {
      id: "accept-release",
      label: "Review release",
      href,
      capability: "projects:approve",
      intent: "approve",
    };
  }
  if (
    context.root === "student" &&
    state === "AWAITING_STUDENT_ACCEPTANCE" &&
    can(context, "offers:decide")
  ) {
    return {
      id: "review-offer",
      label: "Review offer",
      href,
      capability: "offers:decide",
      intent: "review",
    };
  }
  if (
    context.root === "student" &&
    state === "ACTIVE" &&
    can(context, "work:submit")
  ) {
    return {
      id: "continue-project",
      label: "Continue active project",
      href,
      capability: "work:submit",
      intent: "navigate",
    };
  }
  if (
    context.root === "lead" &&
    state === "QA_REVIEW" &&
    can(context, "plans:review")
  ) {
    return {
      id: "review-project",
      label: "Review assignment",
      href,
      capability: "plans:review",
      intent: "review",
    };
  }
  return null;
}

export function resolveWorkspacePrimaryAction(
  context: WorkspaceActionContext,
): WorkspacePrimaryAction | null {
  const currentProject = context.projects?.find((project) =>
    context.path.endsWith(project.id),
  );
  if (currentProject)
    return projectAction(context, currentProject.id, currentProject.state);

  if (context.root === "client" && can(context, "projects:create")) {
    return {
      id: "create-project",
      label: "Create a project",
      href: "/client/projects/new",
      capability: "projects:create",
      intent: "submit",
    };
  }
  if (
    context.root === "student" &&
    context.path === "/student" &&
    can(context, "learning:participate")
  ) {
    return {
      id: "continue-learning",
      label: "Continue learning",
      href: "/student/learn",
      capability: "learning:participate",
      intent: "navigate",
    };
  }
  if (
    context.root === "student" &&
    context.path === "/student/opportunities" &&
    can(context, "opportunities:view")
  ) {
    return {
      id: "review-opportunities",
      label: "Review opportunities",
      href: "/student/opportunities",
      capability: "opportunities:view",
      intent: "review",
    };
  }
  if (
    context.root === "lead" &&
    context.path === "/lead" &&
    can(context, "plans:review")
  ) {
    return {
      id: "review-assignments",
      label: "Review assignments",
      href: "/lead",
      capability: "plans:review",
      intent: "review",
    };
  }
  if (
    context.root === "ops" &&
    context.path === "/ops" &&
    can(context, "approvals:decide")
  ) {
    return {
      id: "review-approvals",
      label: "Review approvals",
      href: "/ops/approvals",
      capability: "approvals:decide",
      intent: "approve",
    };
  }
  if (context.root === "admin" && can(context, "jobs:retry")) {
    return {
      id: "review-jobs",
      label: "Review failed jobs",
      href: "/admin/jobs",
      capability: "jobs:retry",
      intent: "retry",
    };
  }
  if (
    context.root === "university" &&
    can(context, "university:aggregate:view")
  ) {
    return {
      id: "review-outcomes",
      label: "Review outcomes",
      href: "/university",
      capability: "university:aggregate:view",
      intent: "review",
    };
  }
  return null;
}
