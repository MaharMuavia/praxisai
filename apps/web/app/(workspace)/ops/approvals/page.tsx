import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function OperationsApprovalsPage() {
  return (
    <WorkspaceRoute
      path="/ops/approvals"
      title="Approvals"
      description="Review human decisions waiting in the operations queue."
    />
  );
}
