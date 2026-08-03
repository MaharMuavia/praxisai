import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientPage() {
  return (
    <WorkspaceRoute
      path="/client"
      title="Employer workspace"
      description="Projects, decisions, funding, milestones, and released deliverables for the active client organization."
    />
  );
}
