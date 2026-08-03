import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientProjectCreatePage() {
  return (
    <WorkspaceRoute
      path="/client/projects/new"
      title="Create a project"
      description="Capture the outcome, delivery boundaries, and guardrails used to create the immutable client intake snapshot."
    />
  );
}
