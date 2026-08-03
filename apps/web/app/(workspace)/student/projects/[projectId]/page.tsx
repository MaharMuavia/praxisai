import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default async function StudentProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <WorkspaceRoute
      path={`/student/projects/${projectId}`}
      title="Project command center"
      description="Review supervised project work and evidence."
    />
  );
}
