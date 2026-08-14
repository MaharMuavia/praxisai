"use client";

import { praxisFetch, type components } from "@praxisai/api-client";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { type FormEvent, useRef, useState, type ReactNode } from "react";
import { ClientProjectIntake } from "./client-project-intake";
import { EmployerTalentWorkspace } from "./employer-talent-workspace";
import { ProjectCommandCenter } from "./project-command-center";
import {
  RoleWorkspaceRecords,
  type RoleWorkspaceData,
} from "./role-workspace-records";
import { StudentCareerWorkspace } from "./student-career-workspace";
import { WorkspaceOverview } from "./workspace-overview";
import {
  WorkspaceHeader,
  WorkspacePageHeader,
  WorkspaceSidebar,
} from "./workspace-layout";
import { rootFor, visibleNavigation } from "./workspace-navigation";
import { apiBase } from "../lib/api";
import { demoEnvironment } from "../lib/demo-environment";
import type { WorkspaceSearchItem } from "./workspace-command-menu";
import { getSupabaseAuth } from "../lib/supabase";
import { useWorkspaceData } from "./workspace/use-workspace-data";
import { resolveWorkspacePrimaryAction } from "../lib/workspace-actions";

type OperationsJob = components["schemas"]["OperationsJobView"];
type UniversityExport = components["schemas"]["UniversityExportView"];
type NotificationPreference =
  components["schemas"]["NotificationPreferenceView"];
type Offer = components["schemas"]["OfferView"];

export function AppShell({
  path,
  title,
  description,
  children,
}: {
  path: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [exportPurpose, setExportPurpose] = useState("");
  const [recoveryReason, setRecoveryReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [submittingOfferId, setSubmittingOfferId] = useState<string | null>(
    null,
  );
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [globalSearch, setGlobalSearch] = useState("");
  const [logoutBusy, setLogoutBusy] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const mobileTriggerRef = useRef<HTMLButtonElement>(null);
  const root = rootFor(path);
  const projectDetailMatch = path.match(
    /^\/(?:client|student|lead|ops)\/projects\/([0-9a-f-]{36})$/i,
  );
  const projectDetailId = projectDetailMatch?.[1] ?? null;
  const studentCareerPage =
    path === "/student"
      ? "home"
      : path === "/student/learn"
        ? "learn"
        : path === "/student/opportunities"
          ? "opportunities"
          : path === "/student/proposals"
            ? "proposals"
            : null;
  const employerTalentPage =
    path === "/client"
      ? "home"
      : path === "/client/proposals"
        ? "proposals"
        : path === "/client/opportunities/new"
          ? "publish"
          : null;
  const hasCareerWorkspace =
    studentCareerPage !== null || employerTalentPage !== null;
  const isolatedRoute = [
    "/admin/jobs",
    "/student/offers",
    "/lead/offers",
    "/university/exports",
    "/ops/approvals",
    "/ops/risks",
    "/ops/agent-runs",
  ].includes(path);
  const {
    session,
    projects,
    dashboard,
    jobs,
    integrations,
    universityMetrics,
    universityExports,
    notifications,
    notificationPreferences,
    clientInvoices,
    studentCredentials,
    earnings,
    leadReviews,
    approvals,
    risks,
    offers,
    projectWorkspace,
    error,
    isDemoPreview,
    setNotifications,
    setNotificationPreferences,
    setUniversityExports,
    setJobs,
    setOffers,
    setProjectWorkspace,
  } = useWorkspaceData({ path, root, projectDetailId, isolatedRoute });

  const roleWorkspaceData: RoleWorkspaceData | null =
    path === "/client/invoices"
      ? { kind: "invoices", items: clientInvoices }
      : path === "/student/credentials"
        ? { kind: "credentials", items: studentCredentials }
        : path === "/student/earnings" || path === "/lead/earnings"
          ? { kind: "earnings", items: earnings }
          : path === "/lead"
            ? { kind: "reviews", items: leadReviews }
            : path === "/ops/approvals"
              ? { kind: "approvals", items: approvals }
              : path === "/ops/risks"
                ? { kind: "risks", items: risks }
                : path === "/student/offers" || path === "/lead/offers"
                  ? { kind: "offers", items: offers }
                  : null;

  async function decideOffer(offerId: string, decision: "accept" | "decline") {
    setActionError(null);
    setActionNotice(null);
    setSubmittingOfferId(offerId);
    try {
      const updated = await praxisFetch<Offer>(
        apiBase,
        `/assignment-offers/${offerId}/${decision}`,
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({ expected_state: "OFFERED" }),
        },
      );
      setOffers(
        (current) =>
          current?.map((item) => (item.id === updated.id ? updated : item)) ??
          [],
      );
      setActionNotice(
        decision === "accept"
          ? "Offer accepted. Your assignment is now recorded."
          : "Offer declined without reputation impact.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Offer decision failed",
      );
    } finally {
      setSubmittingOfferId(null);
    }
  }

  async function submitUniversityExport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);
    setActionNotice(null);
    setIsSubmitting(true);
    try {
      const created = await praxisFetch<UniversityExport>(
        apiBase,
        "/university/exports",
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({ purpose: exportPurpose }),
        },
      );
      setUniversityExports((current) => [created, ...(current ?? [])]);
      setExportPurpose("");
      setActionNotice("Export request queued with a seven-day expiry.");
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Export request failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function recoverJob(jobId: string) {
    setActionError(null);
    setActionNotice(null);
    setIsSubmitting(true);
    try {
      await praxisFetch<OperationsJob>(apiBase, `/ops/jobs/${jobId}/recover`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ reason: recoveryReason }),
      });
      setJobs((current) => current?.filter((job) => job.id !== jobId) ?? []);
      setRecoveryReason("");
      setActionNotice(
        "Job returned to the pending queue; its attempt history was preserved.",
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error ? reason.message : "Job recovery failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function markNotificationRead(notificationId: string) {
    const item = notifications?.find(
      (notification) => notification.id === notificationId,
    );
    if (!item || item.read_at) return;
    try {
      await praxisFetch<void>(
        apiBase,
        `/notifications/${notificationId}/read`,
        { method: "POST" },
      );
      setNotifications(
        (current) =>
          current?.map((notification) =>
            notification.id === notificationId
              ? { ...notification, read_at: new Date().toISOString() }
              : notification,
          ) ?? [],
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error
          ? reason.message
          : "Unable to mark notification read",
      );
    }
  }

  async function togglePreference(preference: NotificationPreference) {
    setActionError(null);
    try {
      const updated = await praxisFetch<NotificationPreference>(
        apiBase,
        "/notifications/preferences",
        {
          method: "PUT",
          body: JSON.stringify({
            category: preference.category,
            enabled: !preference.enabled,
          }),
        },
      );
      setNotificationPreferences(
        (current) =>
          current?.map((item) =>
            item.category === updated.category ? updated : item,
          ) ?? [],
      );
    } catch (reason: unknown) {
      setActionError(
        reason instanceof Error
          ? reason.message
          : "Unable to update notification preference",
      );
    }
  }

  async function handleLogout() {
    if (logoutBusy) return;
    const correlationId = crypto.randomUUID();
    setLogoutBusy(true);
    setLogoutError(null);
    try {
      await praxisFetch<void>(apiBase, "/auth/logout", {
        method: "POST",
        headers: { "X-Correlation-Id": correlationId },
      });
      if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
        await getSupabaseAuth().signOut();
      }
      await queryClient.cancelQueries();
      queryClient.clear();
      setGlobalSearch("");
      setNotificationOpen(false);
      setMobileNavOpen(false);
      window.history.replaceState(null, "", "/login");
      window.location.replace("/login");
    } catch (reason: unknown) {
      setLogoutError(
        `${reason instanceof Error ? reason.message : "Unable to sign out"}. Support correlation ID: ${correlationId}`,
      );
      setLogoutBusy(false);
    }
  }

  const metricItems: [string, string | number | null | undefined][] =
    root === "university"
      ? [
          ["Participating students", universityMetrics?.participating_students],
          ["Completed projects", universityMetrics?.completed_projects],
          ["Credentials issued", universityMetrics?.credentials_issued],
          [
            "Cohort privacy",
            universityMetrics?.suppressed === undefined
              ? undefined
              : universityMetrics.suppressed
                ? "Suppressed"
                : "Reportable",
          ],
        ]
      : root === "ops" || root === "admin"
        ? [
            ["Pending approvals", dashboard?.pending_approvals],
            ["Failed agent runs", dashboard?.failed_agent_runs],
            ["Dead-letter jobs", dashboard?.dead_letter_jobs],
            ["Payment exceptions", dashboard?.payment_exceptions],
          ]
        : [
            [
              "Active projects",
              projects?.filter((item) => item.state === "ACTIVE").length,
            ],
            [
              "Decisions due",
              projects?.filter((item) => item.state.includes("AWAITING"))
                .length,
            ],
            [
              "Completed",
              projects?.filter((item) => item.state === "COMPLETED").length,
            ],
            ["Environment", session?.environment_label],
          ];

  const searchItems: WorkspaceSearchItem[] = [
    ...visibleNavigation(root, session).map(({ label, href }) => ({
      label,
      href,
      detail: "Workspace navigation",
      kind: "navigation" as const,
    })),
    ...(projects ?? []).map((project) => ({
      label: project.title,
      href: `/${root === "ops" ? "ops" : root}/projects/${project.id}`,
      detail: `${project.category.replaceAll("_", " ")} · loaded project record`,
      kind: "record" as const,
    })),
  ];
  const primaryAction = resolveWorkspacePrimaryAction({
    path,
    root,
    session,
    projects,
  });

  return (
    <div className="app-layout">
      <WorkspaceSidebar
        root={root}
        path={path}
        session={session}
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        mobileTriggerRef={mobileTriggerRef}
      />
      <main className="main">
        <WorkspaceHeader
          root={root}
          title={title}
          session={session}
          notifications={notifications}
          notificationOpen={notificationOpen}
          globalSearch={globalSearch}
          onSearchChange={setGlobalSearch}
          onToggleNotifications={() => setNotificationOpen((open) => !open)}
          onMarkRead={(notificationId) =>
            void markNotificationRead(notificationId)
          }
          onOpenMobileNav={() => setMobileNavOpen(true)}
          mobileTriggerRef={mobileTriggerRef}
          searchItems={searchItems}
          onLogout={() => void handleLogout()}
          logoutBusy={logoutBusy}
          logoutError={logoutError}
        />
        {logoutError ? (
          <div className="error action-message" role="alert">
            {logoutError}
          </div>
        ) : null}
        <div className="app-content">
          <WorkspacePageHeader
            title={title}
            description={description}
            isDemoPreview={
              isDemoPreview || demoEnvironment.showEnvironmentBanner
            }
          />
          {children ?? (
            <>
              {!hasCareerWorkspace && (
                <section className="metric-grid" aria-label="Workspace metrics">
                  {metricItems.map(([label, value]) => (
                    <div className="metric" key={label}>
                      <div className="metric-label">{label}</div>
                      <div className="metric-value">
                        {value === undefined || value === null ? "—" : value}
                      </div>
                    </div>
                  ))}
                </section>
              )}
              {!hasCareerWorkspace && path === `/${root}` && (
                <WorkspaceOverview role={root} />
              )}
              <section
                className={hasCareerWorkspace ? "career-panel" : "panel"}
              >
                <div className="panel-header">
                  <h2>
                    {studentCareerPage
                      ? "Student career workspace"
                      : employerTalentPage
                        ? "Employer hiring workspace"
                        : root === "university"
                          ? "Purpose-limited institutional data"
                          : root === "admin"
                            ? "Provider and job health"
                            : roleWorkspaceData
                              ? "Authorized workspace records"
                              : path === "/client/projects/new"
                                ? "Project intake"
                                : projectDetailId
                                  ? "Project command center"
                                  : "Authorized project records"}
                  </h2>
                  {primaryAction?.href ? (
                    <Link
                      className="button button-primary"
                      href={primaryAction.href}
                    >
                      {primaryAction.label}
                    </Link>
                  ) : null}
                </div>
                {studentCareerPage ? (
                  <StudentCareerWorkspace page={studentCareerPage} />
                ) : employerTalentPage ? (
                  <EmployerTalentWorkspace page={employerTalentPage} />
                ) : path === "/client/projects/new" ? (
                  <ClientProjectIntake />
                ) : error ? (
                  <div className="empty">
                    <div className="error">
                      Workspace API unavailable. Sign in through the demo login
                      or start the API.
                      <br />
                      {error}
                    </div>
                  </div>
                ) : root === "university" ? (
                  universityMetrics === null || universityExports === null ? (
                    <div
                      className="skeleton"
                      aria-label="Loading university data"
                    />
                  ) : universityMetrics.suppressed ? (
                    <div className="empty">
                      Aggregate outcomes are suppressed because the consented
                      cohort is smaller than{" "}
                      {universityMetrics.minimum_cohort_size}. No individual
                      records are exposed.
                    </div>
                  ) : (
                    <>
                      <div className="data-row">
                        <span>
                          <strong>Consented cohort</strong>
                          <small>
                            As of{" "}
                            {new Date(universityMetrics.as_of).toLocaleString()}
                          </small>
                        </span>
                        <span className="status-badge">Reportable</span>
                        <span>
                          <small>Verified work</small>
                          <strong>
                            {universityMetrics.verified_work_minutes ?? 0} min
                          </strong>
                        </span>
                        <span>✓</span>
                      </div>
                      {universityExports.length === 0 ? (
                        <div className="empty">
                          No purpose-limited exports have been requested.
                        </div>
                      ) : (
                        universityExports.map((item) => (
                          <div className="data-row" key={item.id}>
                            <span>
                              <strong>Institutional export</strong>
                              <small>{item.purpose}</small>
                            </span>
                            <span className="status-badge">{item.status}</span>
                            <span>
                              <small>Expires</small>
                              <strong>
                                {new Date(item.expires_at).toLocaleDateString()}
                              </strong>
                            </span>
                            <span>→</span>
                          </div>
                        ))
                      )}
                      <form
                        className="action-form"
                        onSubmit={submitUniversityExport}
                      >
                        <label htmlFor="export-purpose">Export purpose</label>
                        <textarea
                          id="export-purpose"
                          minLength={20}
                          maxLength={2000}
                          onChange={(event) =>
                            setExportPurpose(event.target.value)
                          }
                          required
                          rows={3}
                          value={exportPurpose}
                        />
                        <button
                          className="button button-primary"
                          disabled={isSubmitting || exportPurpose.length < 20}
                          type="submit"
                        >
                          {isSubmitting
                            ? "Requesting…"
                            : "Request expiring export"}
                        </button>
                      </form>
                    </>
                  )
                ) : root === "admin" ? (
                  jobs === null || integrations === null ? (
                    <div
                      className="skeleton"
                      aria-label="Loading platform health"
                    />
                  ) : (
                    <>
                      {integrations.map((item) => (
                        <div className="data-row" key={item.provider}>
                          <span>
                            <strong>
                              {item.provider.replaceAll("_", " ")}
                            </strong>
                            <small>{item.mode} mode</small>
                          </span>
                          <span className="status-badge">
                            {item.configured ? "Configured" : "Needs setup"}
                          </span>
                          <span>
                            <small>External effects</small>
                            <strong>
                              {item.live_side_effects_enabled
                                ? "Enabled"
                                : "Off"}
                            </strong>
                            <small>
                              {item.last_sync_status
                                ? `Last sync: ${item.last_sync_status}`
                                : "No synchronization evidence"}
                            </small>
                          </span>
                          <span>•</span>
                        </div>
                      ))}
                      {jobs.length === 0 && (
                        <div className="empty">
                          No dead-letter jobs require recovery.
                        </div>
                      )}
                      {jobs.length > 0 && (
                        <div className="action-form">
                          <label htmlFor="recovery-reason">
                            Recovery reason
                          </label>
                          <textarea
                            id="recovery-reason"
                            minLength={20}
                            maxLength={2000}
                            onChange={(event) =>
                              setRecoveryReason(event.target.value)
                            }
                            required
                            rows={3}
                            value={recoveryReason}
                          />
                        </div>
                      )}
                      {jobs.map((job) => (
                        <div className="data-row" key={job.id}>
                          <span>
                            <strong>{job.event_type}</strong>
                            <small>{job.last_error ?? "Handler failed"}</small>
                          </span>
                          <span className="status-badge">{job.status}</span>
                          <span>
                            <small>Attempts</small>
                            <strong>{job.attempts}</strong>
                          </span>
                          <button
                            className="button button-ghost"
                            disabled={
                              isSubmitting || recoveryReason.length < 20
                            }
                            onClick={() => void recoverJob(job.id)}
                            type="button"
                          >
                            Recover
                          </button>
                        </div>
                      ))}
                    </>
                  )
                ) : projectDetailId ? (
                  projectWorkspace === null ? (
                    <div
                      className="skeleton"
                      aria-label="Loading project command center"
                    />
                  ) : (
                    <ProjectCommandCenter
                      onWorkspaceChange={setProjectWorkspace}
                      role={session?.active_membership.role ?? ""}
                      workspace={projectWorkspace}
                    />
                  )
                ) : roleWorkspaceData ? (
                  <RoleWorkspaceRecords
                    data={roleWorkspaceData}
                    onOfferDecision={(offerId, decision) =>
                      void decideOffer(offerId, decision)
                    }
                    submittingOfferId={submittingOfferId}
                  />
                ) : projects === null ? (
                  <div className="skeleton" aria-label="Loading projects" />
                ) : projects.length === 0 ? (
                  <div className="empty">
                    No authorized records. Use the valid next action above to
                    begin.
                  </div>
                ) : (
                  projects.map((project) => (
                    <Link
                      className="data-row"
                      href={`/${root === "ops" ? "ops" : root}/projects/${project.id}`}
                      key={project.id}
                    >
                      <span>
                        <strong>{project.title}</strong>
                        <small>
                          {project.category.replaceAll("_", " ")}
                          {project.is_demo ? " · Demo data" : ""}
                        </small>
                      </span>
                      <span className="status-badge">
                        {project.state.replaceAll("_", " ")}
                      </span>
                      <span>
                        <small>Funding guard</small>
                        <strong>
                          {project.currency}{" "}
                          {(
                            project.required_deposit_minor / 100
                          ).toLocaleString()}
                        </strong>
                      </span>
                      <span>→</span>
                    </Link>
                  ))
                )}
              </section>
              {(actionError || actionNotice) && (
                <div
                  className={
                    actionError
                      ? "error action-message"
                      : "success action-message"
                  }
                >
                  {actionError ?? actionNotice}
                </div>
              )}
              {root === "ops" && jobs !== null && (
                <section className="panel">
                  <div className="panel-header">
                    <h2>Dead-letter recovery queue</h2>
                    <Link className="button button-ghost" href="/admin/jobs">
                      Open job operations
                    </Link>
                  </div>
                  {jobs.length === 0 ? (
                    <div className="empty">
                      No dead-letter jobs require recovery.
                    </div>
                  ) : (
                    jobs.map((job) => (
                      <div className="data-row" key={job.id}>
                        <span>
                          <strong>{job.event_type}</strong>
                          <small>
                            {job.aggregate_type} · {job.aggregate_id}
                          </small>
                        </span>
                        <span className="status-badge">{job.status}</span>
                        <span>
                          <small>Attempts</small>
                          <strong>{job.attempts}</strong>
                        </span>
                        <span>→</span>
                      </div>
                    ))
                  )}
                </section>
              )}
              {path.endsWith("/settings") &&
                notificationPreferences !== null && (
                  <section className="panel">
                    <div className="panel-header">
                      <h2>Notification preferences</h2>
                    </div>
                    {notificationPreferences.map((preference) => {
                      const required = [
                        "payments",
                        "credentials",
                        "appeals",
                      ].includes(preference.category);
                      return (
                        <div
                          className="preference-row"
                          key={preference.category}
                        >
                          <span>
                            <strong>{preference.category}</strong>
                            <small>
                              {required
                                ? "Required fairness and financial notice"
                                : "Optional in-app notice"}
                            </small>
                          </span>
                          <button
                            aria-pressed={preference.enabled}
                            className="button button-ghost"
                            disabled={required}
                            onClick={() => void togglePreference(preference)}
                            type="button"
                          >
                            {required
                              ? "Required"
                              : preference.enabled
                                ? "On"
                                : "Off"}
                          </button>
                        </div>
                      );
                    })}
                  </section>
                )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
