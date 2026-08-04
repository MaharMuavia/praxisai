import { queryOptions } from "@tanstack/react-query";
import { internshipFetch, internshipKeys } from "./shared";

export type InternshipCurriculum = {
  track: {
    name: string;
    title: string;
    summary: string;
    skill_outcomes: string[];
  };
  weeks: {
    id: string;
    week_number: number;
    title: string;
    summary: string;
    starts_at: string;
    ends_at: string;
    unlocked: boolean;
    units: {
      id: string;
      title: string;
      summary: string;
      objectives: string[];
      practical_exercise: string;
      completed: boolean;
    }[];
  }[];
};

export const curriculumQuery = () =>
  queryOptions({
    queryKey: internshipKeys.curriculum(),
    queryFn: () =>
      internshipFetch<InternshipCurriculum>("/internships/me/curriculum"),
  });
