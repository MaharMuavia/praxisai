import { AppShell } from "@/components/app-shell";
import { IntakeDetailPage } from "@/features/intake/intake-detail";

export default async function OperationsIntakeDetailPage({
  params,
}: {
  params: Promise<{ submissionId: string }>;
}) {
  const { submissionId } = await params;
  return (
    <AppShell
      path={`/ops/intake/${submissionId}`}
      title="Intake detail"
      description="Review and route one public submission."
    >
      <IntakeDetailPage submissionId={submissionId} />
    </AppShell>
  );
}
