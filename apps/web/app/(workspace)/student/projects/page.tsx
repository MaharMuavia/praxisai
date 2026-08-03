import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function StudentProjectsPage() {
  return (
    <WorkspaceRoute
      path="/student/projects"
      title="My projects"
      description="Review supervised delivery work and evidence."
    />
  );
}
