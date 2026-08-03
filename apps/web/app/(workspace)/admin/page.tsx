import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function AdminPage() {
  return (
    <WorkspaceRoute
      path="/admin"
      title="Platform health"
      description="Review provider health, failed jobs, access controls, and production safety warnings."
    />
  );
}
