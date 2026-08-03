import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function StudentOffersPage() {
  return (
    <AppShell
      path="/student/offers"
      title="Offers"
      description="Review transparent assignment terms before accepting or declining."
    >
      <IsolatedWorkspacePage mode="offers" />
    </AppShell>
  );
}
