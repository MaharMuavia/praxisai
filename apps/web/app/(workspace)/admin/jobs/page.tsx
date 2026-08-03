import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function AdminJobsPage() {
  return (
    <AppShell
      path="/admin/jobs"
      title="Jobs"
      description="Review failed jobs and retry evidence."
    >
      <IsolatedWorkspacePage mode="jobs" />
    </AppShell>
  );
}
