import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function OperationsIntakePage() {
  return (
    <WorkspaceRoute
      path="/ops/intake"
      title="Public intake"
      description="Review public company, student, expert lead, and university submissions."
    />
  );
}
