import { AgentOperationsCenter } from "@/features/operations/agent-operations-center";
import { AppShell } from "@/components/app-shell";

export default function OperationsAgentRunsPage() {
  return (
    <AppShell
      path="/ops/agent-runs"
      title="AI Operations Center"
      description="Review structured agent evidence, validation status, and human approval boundaries."
    >
      <AgentOperationsCenter />
    </AppShell>
  );
}
