import { queryOptions } from "@tanstack/react-query";
import { internshipFetch, internshipKeys } from "./shared";

export type InternshipApplication = {
  id: string;
  cohort_id: string;
  status: string;
  version: number;
  primary_track_id: string | null;
  secondary_track_id: string | null;
  education_status: string;
  university_id: string | null;
  degree_program: string;
  semester_status: string;
  country: string;
  timezone: string;
  weekly_availability_hours: number | null;
  technical_background: string;
  motivation: string;
  portfolio_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  accessibility_requirements: string | null;
  submitted_at: string | null;
  decision_reason: string | null;
  is_demo: boolean;
};

export type InternshipApplicationSummary = Pick<
  InternshipApplication,
  "id" | "status" | "version" | "submitted_at" | "is_demo"
> & {
  program_id: string;
  cohort_id: string;
  decision_at: string | null;
};

export const applicationsQuery = () =>
  queryOptions({
    queryKey: internshipKeys.application(),
    queryFn: () =>
      internshipFetch<InternshipApplicationSummary[]>(
        "/internships/me/applications",
      ),
  });

export const applicationQuery = (applicationId: string) =>
  queryOptions({
    queryKey: [...internshipKeys.application(), applicationId],
    queryFn: () =>
      internshipFetch<InternshipApplication>(
        `/internships/me/applications/${applicationId}`,
      ),
  });
