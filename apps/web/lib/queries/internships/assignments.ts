import { queryOptions } from "@tanstack/react-query";
import { internshipFetch, internshipKeys } from "./shared";

export type InternshipAssignment = {
  id: string;
  title: string;
  summary: string;
  problem_statement: string;
  objectives: string[];
  deliverables: string[];
  acceptance_criteria: string[];
  required_artifact_types: { type: string; required: boolean }[];
  state: string;
  release_at: string;
  due_at: string;
  submitted_at: string | null;
  attempt_count: number;
  current_submission_id: string | null;
  is_late: boolean;
};

export const assignmentsQuery = () =>
  queryOptions({
    queryKey: internshipKeys.assignments(),
    queryFn: () =>
      internshipFetch<InternshipAssignment[]>("/internships/me/assignments"),
  });

export const assignmentQuery = (assignmentId: string) =>
  queryOptions({
    queryKey: ["internships", "assignment", assignmentId] as const,
    queryFn: () =>
      internshipFetch<InternshipAssignment>(
        `/internships/me/assignments/${assignmentId}`,
      ),
    enabled: assignmentId.length > 0,
  });
