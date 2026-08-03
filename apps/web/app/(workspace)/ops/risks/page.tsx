import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function OperationsRisksPage() {
  return (
    <AppShell
      path="/ops/risks"
      title="Risks"
      description="Review open delivery risks and recorded decisions."
    >
      <IsolatedWorkspacePage mode="risks" />
    </AppShell>
  );
}
