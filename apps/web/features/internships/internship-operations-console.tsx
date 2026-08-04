"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, StatusBadge } from "@/components/ui";
import { internshipOperationsApplications } from "@/lib/queries/internships/operations";

type OperationsApplication = {
  id: string;
  applicant_display_name: string;
  applicant_email: string;
  status: string;
  degree_program: string;
  is_demo: boolean;
};

export function InternshipOperationsConsole() {
  const query = useQuery({
    queryKey: ["internships", "operations", "applications"],
    queryFn: internshipOperationsApplications,
  });
  if (query.isLoading)
    return <div className="internship-loading">Loading admissions queue…</div>;
  if (query.isError)
    return (
      <div className="internship-error" role="alert">
        The operations queue is unavailable or you do not have access.
      </div>
    );
  const applications = (query.data ?? []) as OperationsApplication[];
  return (
    <main className="internship-portal" id="main-content">
      <header className="internship-portal-header">
        <div>
          <span className="marketing-eyebrow">Operations control center</span>
          <h1>Internship admissions and review.</h1>
          <p>
            Applications, reviewer workload, cohort progress, and completion
            decisions stay inside the operations boundary.
          </p>
        </div>
        <span className="internship-demo-label">Privacy-scoped queue</span>
      </header>
      <section className="internship-section">
        <Card>
          <div className="internship-section-heading">
            <div>
              <span className="marketing-eyebrow">Admissions</span>
              <h2>Human decision queue</h2>
            </div>
            <StatusBadge tone="ai">No AI decisions</StatusBadge>
          </div>
          <div className="internship-assignment-list">
            {applications.map((application) => (
              <article className="internship-unit" key={application.id}>
                <div>
                  <span className="internship-unit-type">
                    {application.is_demo ? "Demo data" : "Application"}
                  </span>
                  <h3>{application.applicant_display_name}</h3>
                  <p>
                    {application.degree_program || "Education details pending"}{" "}
                    · {application.applicant_email}
                  </p>
                </div>
                <StatusBadge
                  tone={
                    application.status === "ACCEPTED" ? "success" : "warning"
                  }
                >
                  {application.status.replaceAll("_", " ")}
                </StatusBadge>
              </article>
            ))}
          </div>
          {applications.length === 0 ? (
            <div className="internship-empty">
              No applications are currently in the queue.
            </div>
          ) : null}
        </Card>
      </section>
    </main>
  );
}
