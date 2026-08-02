import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  BriefcaseBusiness,
  FileCheck2,
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
export type NavigationItem = readonly [
  label: string,
  href: string,
  icon: LucideIcon,
];

export const navigation: Record<WorkspaceRoot, readonly NavigationItem[]> = {
  client: [
    ["Overview", "/client", LayoutDashboard],
    ["Projects", "/client/projects", BriefcaseBusiness],
    ["Student proposals", "/client/proposals", Users],
    ["Publish opportunity", "/client/opportunities/new", Send],
    ["Invoices", "/client/invoices", FileCheck2],
    ["Organization", "/client/organization", Users],
  ],
  student: [
    ["Overview", "/student", LayoutDashboard],
    ["Learn", "/student/learn", BookOpen],
    ["Paid projects", "/student/opportunities", Search],
    ["My proposals", "/student/proposals", Send],
    ["Offers", "/student/offers", FileCheck2],
    ["Projects", "/student/projects", BriefcaseBusiness],
    ["Earnings", "/student/earnings", FileCheck2],
    ["Credentials", "/student/credentials", Shield],
  ],
  lead: [
    ["Overview", "/lead", LayoutDashboard],
    ["Offers", "/lead/offers", FileCheck2],
    ["Reviews", "/lead", BriefcaseBusiness],
    ["Earnings", "/lead/earnings", Shield],
  ],
  ops: [
    ["Operations", "/ops", LayoutDashboard],
    ["Approvals", "/ops/approvals", FileCheck2],
    ["Risks", "/ops/risks", Shield],
    ["Projects", "/ops/projects", BriefcaseBusiness],
    ["People", "/ops/students", Users],
    ["Agent runs", "/ops/agent-runs", Shield],
  ],
  admin: [
    ["Platform health", "/admin", LayoutDashboard],
    ["Access", "/admin/access", Users],
    ["Integrations", "/admin/integrations", Settings],
    ["Jobs", "/admin/jobs", BriefcaseBusiness],
  ],
  university: [
    ["Outcomes", "/university", LayoutDashboard],
    ["Students", "/university/students", Users],
    ["Exports", "/university/exports", FileCheck2],
    ["Settings", "/university/settings", Settings],
  ],
};

export function rootFor(path: string): WorkspaceRoot {
  if (path.startsWith("/student")) return "student";
  if (path.startsWith("/lead")) return "lead";
  if (path.startsWith("/ops")) return "ops";
  if (path.startsWith("/admin")) return "admin";
  if (path.startsWith("/university")) return "university";
  return "client";
}
