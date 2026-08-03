import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientOpportunityPage() {
  return (
    <WorkspaceRoute
      path="/client/opportunities/new"
      title="Publish a paid project"
      description="Give students the business context, deliverables, skills, supervision, budget, and proposal requirements they need."
    />
  );
}
