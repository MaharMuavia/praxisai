import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default async function LeadProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <WorkspaceRoute
      path={`/lead/projects/${projectId}`}
      title="Project review"
      description="Review project risks, QA findings, and release recommendations."
    />
  );
}
