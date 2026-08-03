"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { useMemo, type SetStateAction } from "react";
import { demoWorkspaceSnapshot, withDemoFallback } from "../../lib/demo-data";
import { fetchQuery, retryTransientError } from "../../lib/queries/shared";

type Session = components["schemas"]["SessionView"];
type Project = components["schemas"]["ProjectView"];
type Dashboard = components["schemas"]["DashboardSummary"];
type OperationsJob = components["schemas"]["OperationsJobView"];
type Integration = components["schemas"]["IntegrationStatus"];
type UniversityMetrics = components["schemas"]["UniversityMetrics"];
type UniversityExport = components["schemas"]["UniversityExportView"];
type Notification = components["schemas"]["NotificationView"];
type NotificationPreference =
  components["schemas"]["NotificationPreferenceView"];
type ClientInvoice = components["schemas"]["ClientInvoiceView"];
type StudentCredential = components["schemas"]["StudentCredentialView"];
type EarningsItem = components["schemas"]["EarningsItemView"];
type LeadReviewQueueItem = components["schemas"]["LeadReviewQueueItem"];
type ApprovalQueueItem = components["schemas"]["ApprovalQueueItem"];
type RiskQueueItem = components["schemas"]["RiskQueueItem"];
type Offer = components["schemas"]["OfferView"];
type ProjectWorkspace = components["schemas"]["ProjectWorkspaceView"];

type QueryResult<T> = { data: T; isDemo: boolean };

function useWorkspaceQuery<T>(
  key: readonly unknown[],
  path: string,
  enabled = true,
  fallback?: T,
) {
  return useQuery<QueryResult<T>>({
    queryKey: key,
    enabled,
    queryFn: async ({ signal }) => {
      const request = fetchQuery<T>(path, signal);
      if (fallback === undefined) {
        return { data: await request, isDemo: false };
      }
      return withDemoFallback(request, fallback);
    },
    retry: retryTransientError,
  });
}

function useQuerySetter<T>(
  queryClient: ReturnType<typeof useQueryClient>,
  key: readonly unknown[],
) {
  return (next: SetStateAction<T | null>) => {
    queryClient.setQueryData<QueryResult<T>>(key, (current) => {
      const currentValue = current?.data ?? null;
      const value =
        typeof next === "function"
          ? (next as (value: T | null) => T | null)(currentValue)
          : next;
      return value === null
        ? undefined
        : { data: value, isDemo: current?.isDemo ?? false };
    });
  };
}

function errorMessage(error: unknown): string | null {
  return error instanceof Error ? error.message : null;
}

export function useWorkspaceData({
  path,
  root,
  projectDetailId,
}: {
  path: string;
  root: string;
  projectDetailId: string | null;
}) {
  const queryClient = useQueryClient();
  const sessionQuery = useWorkspaceQuery<Session>(
    ["auth", "session"],
    "/auth/me",
    true,
    demoWorkspaceSnapshot.session,
  );
  const notificationsQuery = useWorkspaceQuery<Notification[]>(
    ["notifications", "list"],
    "/notifications",
    true,
    demoWorkspaceSnapshot.notifications,
  );
  const preferencesQuery = useWorkspaceQuery<NotificationPreference[]>(
    ["notifications", "preferences"],
    "/notifications/preferences",
    true,
    demoWorkspaceSnapshot.notificationPreferences,
  );
  const projectsQuery = useWorkspaceQuery<{ items: Project[] }>(
    ["projects", "list"],
    "/projects",
    root !== "university",
    { items: demoWorkspaceSnapshot.projects },
  );
  const universityMetricsQuery = useWorkspaceQuery<UniversityMetrics>(
    ["university", "metrics"],
    "/university/metrics",
    root === "university",
  );
  const universityExportsQuery = useWorkspaceQuery<UniversityExport[]>(
    ["university", "exports"],
    "/university/exports",
    root === "university",
  );
  const dashboardQuery = useWorkspaceQuery<Dashboard>(
    ["operations", "dashboard"],
    "/ops/dashboard",
    root === "ops" || root === "admin",
  );
  const jobsQuery = useWorkspaceQuery<OperationsJob[]>(
    ["operations", "jobs"],
    "/ops/jobs?status=DEAD_LETTER",
    root === "ops" || root === "admin",
  );
  const integrationsQuery = useWorkspaceQuery<Integration[]>(
    ["operations", "integrations"],
    "/ops/integrations",
    root === "ops" || root === "admin",
  );
  const invoicesQuery = useWorkspaceQuery<ClientInvoice[]>(
    ["billing", "invoices"],
    "/client/invoices",
    path === "/client/invoices",
  );
  const credentialsQuery = useWorkspaceQuery<StudentCredential[]>(
    ["credentials", "mine"],
    "/students/me/credentials",
    path === "/student/credentials",
  );
  const earningsQuery = useWorkspaceQuery<EarningsItem[]>(
    ["billing", "earnings"],
    "/participants/me/earnings",
    path === "/student/earnings" || path === "/lead/earnings",
  );
  const reviewsQuery = useWorkspaceQuery<LeadReviewQueueItem[]>(
    ["lead", "review-queue"],
    "/leads/me/review-queue",
    path === "/lead",
  );
  const approvalsQuery = useWorkspaceQuery<ApprovalQueueItem[]>(
    ["operations", "approvals"],
    "/ops/approval-queue",
    path === "/ops/approvals",
  );
  const risksQuery = useWorkspaceQuery<RiskQueueItem[]>(
    ["operations", "risks"],
    "/ops/risk-queue",
    path === "/ops/risks",
  );
  const offersQuery = useWorkspaceQuery<Offer[]>(
    ["offers", "list"],
    "/assignment-offers",
    path === "/student/offers" || path === "/lead/offers",
  );
  const projectWorkspaceQuery = useWorkspaceQuery<ProjectWorkspace>(
    ["projects", "workspace", projectDetailId],
    `/projects/${projectDetailId}/workspace`,
    projectDetailId !== null,
  );

  const routeError = useMemo(() => {
    const queries =
      root === "university"
        ? [universityMetricsQuery, universityExportsQuery]
        : root === "admin"
          ? [dashboardQuery, jobsQuery, integrationsQuery]
          : projectDetailId !== null
            ? [projectWorkspaceQuery]
            : path === "/client/invoices"
              ? [invoicesQuery]
              : path === "/student/credentials"
                ? [credentialsQuery]
                : path === "/student/earnings" || path === "/lead/earnings"
                  ? [earningsQuery]
                  : path === "/lead"
                    ? [reviewsQuery]
                    : path === "/ops/approvals"
                      ? [approvalsQuery]
                      : path === "/ops/risks"
                        ? [risksQuery]
                        : path === "/student/offers" || path === "/lead/offers"
                          ? [offersQuery]
                          : root === "ops" && path === "/ops"
                            ? [dashboardQuery, jobsQuery, integrationsQuery]
                            : [projectsQuery];
    return (
      queries.map((query) => errorMessage(query.error)).find(Boolean) ??
      errorMessage(sessionQuery.error)
    );
  }, [
    approvalsQuery,
    credentialsQuery,
    dashboardQuery,
    earningsQuery,
    integrationsQuery,
    invoicesQuery,
    jobsQuery,
    offersQuery,
    path,
    projectDetailId,
    projectWorkspaceQuery,
    projectsQuery,
    reviewsQuery,
    risksQuery,
    root,
    sessionQuery.error,
    universityExportsQuery,
    universityMetricsQuery,
  ]);

  return {
    session: sessionQuery.data?.data ?? null,
    projects: projectsQuery.data?.data.items ?? null,
    dashboard: dashboardQuery.data?.data ?? null,
    jobs: jobsQuery.data?.data ?? null,
    integrations: integrationsQuery.data?.data ?? null,
    universityMetrics: universityMetricsQuery.data?.data ?? null,
    universityExports: universityExportsQuery.data?.data ?? null,
    notifications: notificationsQuery.data?.data ?? null,
    notificationPreferences: preferencesQuery.data?.data ?? null,
    clientInvoices: invoicesQuery.data?.data ?? null,
    studentCredentials: credentialsQuery.data?.data ?? null,
    earnings: earningsQuery.data?.data ?? null,
    leadReviews: reviewsQuery.data?.data ?? null,
    approvals: approvalsQuery.data?.data ?? null,
    risks: risksQuery.data?.data ?? null,
    offers: offersQuery.data?.data ?? null,
    projectWorkspace: projectWorkspaceQuery.data?.data ?? null,
    error: routeError,
    isDemoPreview: [
      sessionQuery,
      notificationsQuery,
      preferencesQuery,
      projectsQuery,
    ].some((query) => query.data?.isDemo === true),
    setNotifications: useQuerySetter<Notification[]>(queryClient, [
      "notifications",
      "list",
    ]),
    setNotificationPreferences: useQuerySetter<NotificationPreference[]>(
      queryClient,
      ["notifications", "preferences"],
    ),
    setUniversityExports: useQuerySetter<UniversityExport[]>(queryClient, [
      "university",
      "exports",
    ]),
    setJobs: useQuerySetter<OperationsJob[]>(queryClient, [
      "operations",
      "jobs",
    ]),
    setOffers: useQuerySetter<Offer[]>(queryClient, ["offers", "list"]),
    setProjectWorkspace: useQuerySetter<ProjectWorkspace>(queryClient, [
      "projects",
      "workspace",
      projectDetailId,
    ]),
  };
}
