import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientProjectsPage() {
  return (
    <WorkspaceRoute
      path="/client/projects"
      title="Projects"
      description="Review the active project pipeline and the next accountable client decision."
    />
  );
}
