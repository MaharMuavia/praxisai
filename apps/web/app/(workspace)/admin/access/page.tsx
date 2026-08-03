import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function AdminAccessPage() {
  return (
    <WorkspaceRoute
      path="/admin/access"
      title="Access"
      description="Review platform access controls and memberships."
    />
  );
}
