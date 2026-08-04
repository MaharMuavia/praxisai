import { InternshipStudentPortal } from "@/features/internships/internship-student-portal";

export default async function InternshipAssignmentPage({
  params,
}: {
  params: Promise<{ assignmentId: string }>;
}) {
  const { assignmentId } = await params;
  return (
    <InternshipStudentPortal view="assignments" assignmentId={assignmentId} />
  );
}
