import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function OperationsAgentRunsPage() {
  return (
    <WorkspaceRoute
      path="/ops/agent-runs"
      title="Agent runs"
      description="Review structured agent evidence and validation status."
    />
  );
}
