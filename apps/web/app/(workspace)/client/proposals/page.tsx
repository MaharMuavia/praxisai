import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientProposalsPage() {
  return (
    <WorkspaceRoute
      path="/client/proposals"
      title="Student proposals"
      description="Compare each proposal's approach, delivery plan, evidence, price, and availability."
    />
  );
}
