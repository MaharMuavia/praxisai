import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function OperationsPage() {
  return (
    <WorkspaceRoute
      path="/ops"
      title="Operations"
      description="Review approvals, delivery risk, funding exceptions, agent evidence, and audit history."
    />
  );
}
