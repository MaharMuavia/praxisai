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

export type VisualDefect = {
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  location_or_element?: string | null;
};

export type VisualCriterionFinding = {
  criterion_ordinal: number;
  passed: boolean;
  confidence_score: number;
  visual_evidence_summary: string;
  observed_features: string[];
  defects: VisualDefect[];
};

export type SubmissionAIReviewResponse = {
  submission_id: string;
  agent_run_id: string;
  model_identifier: string;
  recommendation: string;
  overall_visual_score: number;
  summary: string;
  criterion_findings: VisualCriterionFinding[];
  identified_defects: VisualDefect[];
  student_actionable_feedback: string[];
  latency_ms: number;
  is_demo: boolean;
  created_at: string;
};

export function requestSubmissionAIReview(
  submissionId: string,
  rubricFocus: string[] = [],
) {
  return internshipFetch<SubmissionAIReviewResponse>(
    `/internships/me/submissions/${submissionId}/ai-review`,
    {
      method: "POST",
      body: JSON.stringify({ rubric_focus: rubricFocus }),
    },
  );
}
