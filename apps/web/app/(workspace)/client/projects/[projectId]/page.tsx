import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default async function ClientProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <WorkspaceRoute
      path={`/client/projects/${projectId}`}
      title="Project command center"
      description="Review project scope, delivery evidence, decisions, and release state."
    />
  );
}
