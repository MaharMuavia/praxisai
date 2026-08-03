import type { components } from "@praxisai/api-client";

export type WorkspacePrimaryAction = {
  id: string;
  label: string;
  href?: string;
  capability?: string;
  disabled?: boolean;
  disabledReason?: string;
  intent:
    | "navigate"
    | "submit"
    | "approve"
    | "review"
    | "upload"
    | "retry"
    | "accept"
    | "decline";
};

export type WorkspaceActionContext = {
  path: string;
  root: "client" | "student" | "lead" | "ops" | "admin" | "university";
  session: components["schemas"]["SessionView"] | null;
  projects: components["schemas"]["ProjectView"][] | null;
};
