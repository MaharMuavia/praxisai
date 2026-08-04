import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  BriefcaseBusiness,
  FileCheck2,
  GraduationCap,
  LayoutDashboard,
  Send,
  Settings,
  Search,
  Shield,
  Users,
} from "lucide-react";

export type WorkspaceRoot =
  | "client"
  | "student"
  | "lead"
  | "ops"
  | "admin"
  | "university";
export type WorkspaceNavigationItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  requiredCapabilities?: string[];
  match: (pathname: string) => boolean;
};

type SessionNavigationContext = {
  capabilities?: string[] | null;
};

const item = (
  label: string,
  href: string,
  icon: LucideIcon,
  requiredCapabilities?: string[],
): WorkspaceNavigationItem => ({
  label,
  href,
  icon,
  requiredCapabilities,
  match: (pathname) => isNavigationItemActive(pathname, href, label),
});

export function isNavigationItemActive(
  path: string,
  href: string,
  label?: string,
): boolean {
  if (label === "Reviews" && href === "/lead") {
    return (
      path.startsWith("/lead") &&
      path !== "/lead/offers" &&
      path !== "/lead/earnings"
    );
  }
  const isRootRoute = href.split("/").filter(Boolean).length === 1;
  return isRootRoute
    ? path === href
    : path === href || path.startsWith(`${href}/`);
}

export const navigation: Record<
  WorkspaceRoot,
  readonly WorkspaceNavigationItem[]
> = {
  client: [
    item("Overview", "/client", LayoutDashboard, ["projects:view"]),
    item("Projects", "/client/projects", BriefcaseBusiness, ["projects:view"]),
    item("Student proposals", "/client/proposals", Users, ["proposals:decide"]),
    item("Publish opportunity", "/client/opportunities/new", Send, [
      "opportunities:publish",
    ]),
    item("Invoices", "/client/invoices", FileCheck2, ["payments:view"]),
    item("Organization", "/client/organization", Users, ["members:manage"]),
  ],
  student: [
    item("Overview", "/student", LayoutDashboard),
    item("Internship", "/student/internship", GraduationCap, [
      "internships:view_own",
    ]),
    item("Learn", "/student/learn", BookOpen, ["learning:participate"]),
    item("Paid projects", "/student/opportunities", Search, [
      "opportunities:view",
    ]),
    item("My proposals", "/student/proposals", Send, ["proposals:create"]),
    item("Offers", "/student/offers", FileCheck2, ["offers:decide"]),
    item("Projects", "/student/projects", BriefcaseBusiness, ["work:submit"]),
    item("Earnings", "/student/earnings", FileCheck2),
    item("Credentials", "/student/credentials", Shield, ["credentials:view"]),
  ],
  lead: [
    item("Overview", "/lead", LayoutDashboard),
    item("Offers", "/lead/offers", FileCheck2, ["offers:decide"]),
    item("Reviews", "/lead", BriefcaseBusiness, ["plans:review"]),
    item("Earnings", "/lead/earnings", Shield),
  ],
  ops: [
    item("Operations", "/ops", LayoutDashboard, ["projects:operate"]),
    item("Internships", "/ops/internships", GraduationCap, [
      "internships:view_analytics",
    ]),
    item("Approvals", "/ops/approvals", FileCheck2, ["approvals:decide"]),
    item("Risks", "/ops/risks", Shield, ["projects:operate"]),
    item("Projects", "/ops/projects", BriefcaseBusiness, ["projects:operate"]),
    item("People", "/ops/students", Users, ["projects:operate"]),
    item("Agent runs", "/ops/agent-runs", Shield, ["projects:operate"]),
    item("Intake", "/ops/intake", Users, ["projects:operate"]),
  ],
  admin: [
    item("Platform health", "/admin", LayoutDashboard, ["platform:configure"]),
    item("Access", "/admin/access", Users, ["access:manage"]),
    item("Integrations", "/admin/integrations", Settings, [
      "platform:configure",
    ]),
    item("Jobs", "/admin/jobs", BriefcaseBusiness, ["jobs:retry"]),
  ],
  university: [
    item("Outcomes", "/university", LayoutDashboard, [
      "university:aggregate:view",
    ]),
    item("Students", "/university/students", Users, [
      "university:consented:view",
    ]),
    item("Exports", "/university/exports", FileCheck2, [
      "university:consented:view",
    ]),
    item("Settings", "/university/settings", Settings, [
      "university:aggregate:view",
    ]),
  ],
};

export function visibleNavigation(
  root: WorkspaceRoot,
  session: SessionNavigationContext | null,
) {
  if (session === null) return navigation[root];
  const capabilities = new Set(session?.capabilities ?? []);
  return navigation[root].filter((entry) =>
    (entry.requiredCapabilities ?? []).every((capability) =>
      capabilities.has(capability),
    ),
  );
}

export function rootFor(path: string): WorkspaceRoot {
  if (path.startsWith("/student")) return "student";
  if (path.startsWith("/lead")) return "lead";
  if (path.startsWith("/ops")) return "ops";
  if (path.startsWith("/admin")) return "admin";
  if (path.startsWith("/university")) return "university";
  return "client";
}
