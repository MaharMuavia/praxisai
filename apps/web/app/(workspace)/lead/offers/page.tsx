import { AppShell } from "@/components/app-shell";
import { IsolatedWorkspacePage } from "@/features/workspace/isolated-workspace-page";
export default function LeadOffersPage() {
  return (
    <AppShell
      path="/lead/offers"
      title="Offers"
      description="Review supervision offers and visible terms."
    >
      <IsolatedWorkspacePage mode="offers" />
    </AppShell>
  );
}
