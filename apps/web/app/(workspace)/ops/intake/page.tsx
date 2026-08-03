import { AppShell } from "@/components/app-shell";
import { IntakeQueuePage } from "@/features/intake/intake-queue";
export default function OperationsIntakePage() {
  return (
    <AppShell
      path="/ops/intake"
      title="Public intake"
      description="Review public company, student, expert lead, and university submissions."
    >
      <IntakeQueuePage />
    </AppShell>
  );
}
