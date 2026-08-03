import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function StudentEarningsPage() {
  return (
    <WorkspaceRoute
      path="/student/earnings"
      title="Earnings"
      description="Review recorded compensation and payout evidence."
    />
  );
}
