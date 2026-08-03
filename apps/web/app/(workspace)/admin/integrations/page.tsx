import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function AdminIntegrationsPage() {
  return (
    <WorkspaceRoute
      path="/admin/integrations"
      title="Integrations"
      description="Review provider configuration and synchronization evidence."
    />
  );
}
