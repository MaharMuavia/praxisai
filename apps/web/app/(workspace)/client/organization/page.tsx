import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientOrganizationPage() {
  return (
    <WorkspaceRoute
      path="/client/organization"
      title="Organization"
      description="Review organization membership and notification settings."
    />
  );
}
