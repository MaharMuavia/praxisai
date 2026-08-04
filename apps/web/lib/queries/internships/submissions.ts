import { internshipFetch } from "./shared";

export type SubmissionDraft = {
  id: string;
  version: number;
  state: string;
  links: Record<string, string>;
  text_fields: Record<string, string>;
  artifact_upload_ids: string[];
  canonical_hash: string | null;
};

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
