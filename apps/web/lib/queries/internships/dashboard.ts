import { queryOptions } from "@tanstack/react-query";
import { internshipFetch, internshipKeys, type Dashboard } from "./shared";

export const dashboardQuery = () =>
  queryOptions({
    queryKey: internshipKeys.dashboard(),
    queryFn: () => internshipFetch<Dashboard>("/internships/me/dashboard"),
  });
