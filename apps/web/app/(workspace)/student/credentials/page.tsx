import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function StudentCredentialsPage() {
  return (
    <WorkspaceRoute
      path="/student/credentials"
      title="Credentials"
      description="Review verified credentials and public verification controls."
    />
  );
}
