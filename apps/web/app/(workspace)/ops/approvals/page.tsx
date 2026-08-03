import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function OperationsApprovalsPage() {
  return (
    <AppShell
      path="/ops/approvals"
      title="Approvals"
      description="Review human decisions waiting in the operations queue."
    >
      <IsolatedWorkspacePage mode="approvals" />
    </AppShell>
  );
}
