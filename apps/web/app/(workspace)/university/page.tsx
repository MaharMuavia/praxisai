import { AppShell } from "@/components/app-shell";
import { UniversityAnalyticsPortal } from "@/features/university/university-analytics-portal";

export default function UniversityPage() {
  return (
    <AppShell
      path="/university"
      title="Outcomes"
      description="Review consented student evidence and privacy-safe cohort outcomes."
    >
      <UniversityAnalyticsPortal />
    </AppShell>
  );
}
