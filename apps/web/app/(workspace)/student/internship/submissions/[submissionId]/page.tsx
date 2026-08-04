import { InternshipSubmissionEditor } from "@/features/internships/internship-submission-editor";

export default async function InternshipSubmissionPage({
  params,
}: {
  params: Promise<{ submissionId: string }>;
}) {
  const { submissionId } = await params;
  return <InternshipSubmissionEditor submissionId={submissionId} />;
}
