import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function AdminJobsPage() {
  return (
    <WorkspaceRoute
      path="/admin/jobs"
      title="Jobs"
      description="Review failed jobs and retry evidence."
    />
  );
}
