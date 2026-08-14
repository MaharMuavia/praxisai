import { queryOptions } from "@tanstack/react-query";
import { praxisFetch } from "@praxisai/api-client";
import { apiBase } from "../../api";

export type InternshipProgram = {
  id: string;
  slug: string;
  name: string;
  public_description: string;
  status: string;
  duration_weeks: number;
  default_timezone: string;
  is_demo: boolean;
};

export type InternshipProgramDetail = InternshipProgram & {
  cohorts: {
    id: string;
    name: string;
    slug: string;
    status: string;
    starts_at: string;
    ends_at: string;
    application_deadline: string | null;
    capacity: number;
    timezone: string;
    is_demo: boolean;
  }[];
  tracks: {
    id: string;
    name: string;
    slug: string;
    version_id: string;
    version: number;
    title: string;
    summary: string;
    skill_outcomes: string[];
    expected_weekly_hours: number;
  }[];
};

export type Dashboard = {
  enrollment_id: string | null;
  program_name: string | null;
  cohort_name: string | null;
  track: { name: string; title: string; skill_outcomes: string[] } | null;
  enrollment_status: string | null;
  certificate_eligibility: string | null;
  completed_units: number;
  required_units: number;
  passed_assignments: number;
  required_assignments: number;
  progress_percent: number;
  timeline: { label: string; state: string }[];
  is_demo: boolean;
};

export const internshipKeys = {
  all: ["internships"] as const,
  programs: () => [...internshipKeys.all, "programs"] as const,
  program: (slug: string) => [...internshipKeys.programs(), slug] as const,
  application: () => [...internshipKeys.all, "application"] as const,
  dashboard: () => [...internshipKeys.all, "dashboard"] as const,
  curriculum: () => [...internshipKeys.all, "curriculum"] as const,
  assignments: () => [...internshipKeys.all, "assignments"] as const,
  feedback: () => [...internshipKeys.all, "feedback"] as const,
  certificate: () => [...internshipKeys.all, "certificate"] as const,
};

export async function internshipFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  return praxisFetch<T>(apiBase, path, init);
}

export const programsQuery = () =>
  queryOptions({
    queryKey: internshipKeys.programs(),
    queryFn: () =>
      internshipFetch<InternshipProgram[]>("/internships/programs"),
  });

export const programQuery = (slug: string) =>
  queryOptions({
    queryKey: internshipKeys.program(slug),
    queryFn: () =>
      internshipFetch<InternshipProgramDetail>(`/internships/programs/${slug}`),
  });
