import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default async function OperationsProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <WorkspaceRoute
      path={`/ops/projects/${projectId}`}
      title="Project command center"
      description="Review project evidence and operational decisions."
    />
  );
}
