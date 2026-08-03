import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function OperationsRisksPage() {
  return (
    <WorkspaceRoute
      path="/ops/risks"
      title="Risks"
      description="Review open delivery risks and recorded decisions."
    />
  );
}
