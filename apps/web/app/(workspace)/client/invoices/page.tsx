import { WorkspaceRoute } from "@/components/workspace/workspace-route";
export default function ClientInvoicesPage() {
  return (
    <WorkspaceRoute
      path="/client/invoices"
      title="Invoices"
      description="Review recorded project charges and funding evidence for the active organization."
    />
  );
}
