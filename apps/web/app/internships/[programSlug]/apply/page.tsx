import { StudentSignup } from "@/features/internships/internship-public";
import { Suspense } from "react";

export default function InternshipApplyPage() {
  return (
    <Suspense
      fallback={<div className="internship-loading">Loading signup…</div>}
    >
      <StudentSignup />
    </Suspense>
  );
}
