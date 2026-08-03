import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function UniversityExportsPage() {
  return (
    <AppShell
      path="/university/exports"
      title="Exports"
      description="Review purpose-limited institutional exports."
    >
      <IsolatedWorkspacePage mode="exports" />
    </AppShell>
  );
}
