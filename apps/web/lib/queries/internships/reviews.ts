import { queryOptions } from "@tanstack/react-query";
import { internshipFetch, internshipKeys } from "./shared";

export type InternshipFeedback = {
  review_id: string;
  assignment_id: string;
  submission_id: string;
  decision: string;
  weighted_total: number;
  student_feedback: string;
  finalized_at: string;
};

export const feedbackQuery = () =>
  queryOptions({
    queryKey: internshipKeys.feedback(),
    queryFn: () =>
      internshipFetch<InternshipFeedback[]>("/internships/me/feedback"),
  });
