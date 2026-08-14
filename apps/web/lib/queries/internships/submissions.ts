import { internshipFetch } from "./shared";

export type SubmissionDraft = {
  id: string;
  student_assignment_id: string;
  version: number;
  state: string;
  links: Record<string, string>;
  text_fields: Record<string, string>;
  artifact_upload_ids: string[];
  canonical_hash: string | null;
};

export type SubmissionUpdate = {
  expected_version: number;
  links: Record<string, string>;
  text_fields: Record<string, string>;
  artifact_upload_ids: string[];
};

export function getInternshipSubmission(submissionId: string) {
  return internshipFetch<SubmissionDraft>(
    `/internships/me/submissions/${submissionId}`,
  );
}

export function updateInternshipSubmission(
  submissionId: string,
  body: SubmissionUpdate,
) {
  return internshipFetch<SubmissionDraft>(
    `/internships/me/submissions/${submissionId}`,
    { method: "PUT", body: JSON.stringify(body) },
  );
}

export function saveInternshipDraft(assignmentId: string, body: unknown) {
  return internshipFetch<SubmissionDraft>(
    `/internships/me/assignments/${assignmentId}/submission-drafts`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export function finalizeInternshipSubmission(
  submissionId: string,
  body: unknown,
  idempotencyKey: string,
) {
  return internshipFetch<SubmissionDraft>(
    `/internships/me/submissions/${submissionId}/finalize`,
    {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Idempotency-Key": idempotencyKey },
    },
  );
}
