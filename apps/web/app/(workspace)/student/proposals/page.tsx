import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function StudentProposalsPage() {
  return (
    <WorkspaceRoute
      path="/student/proposals"
      title="My project proposals"
      description="Track every proposal and employer decision."
    />
  );
}
