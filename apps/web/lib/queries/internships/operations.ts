import { internshipFetch } from "./shared";

export function internshipOperationsApplications() {
  return internshipFetch<unknown[]>("/ops/internships/applications");
}
