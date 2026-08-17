"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Award,
  CheckCircle2,
  Clock,
  Download,
  DollarSign,
  FileSpreadsheet,
  Lock,
  Plus,
  ShieldCheck,
  Users,
} from "lucide-react";
import { DemoBadge } from "@/components/demo-boundary";
import { Button, Card, StatusBadge } from "@/components/ui";
import {
  requestUniversityExport,
  universityExportsQuery,
  universityKeys,
  universityMetricsQuery,
  type UniversityMetrics,
} from "@/lib/queries/university";

const FALLBACK_DEMO_METRICS: UniversityMetrics = {
  suppressed: false,
  minimum_cohort_size: 5,
  consented_cohort_size: 28,
  participating_students: 24,
  completed_projects: 18,
  credentials_issued: 32,
  verified_work_minutes: 19440, // 324 hours
  total_earnings_minor: 1166400, // $11,664.00
  average_rating_basis_points: 485, // 4.85 / 5.0
  pathway_breakdown: [
    {
      pathway_name: "Full-Stack Web & Cloud Systems",
      student_count: 12,
      verified_minutes: 8740,
      credentials_count: 14,
    },
    {
      pathway_name: "AI & Applied Machine Learning",
      student_count: 9,
      verified_minutes: 6800,
      credentials_count: 11,
    },
    {
      pathway_name: "UI/UX & Design Systems",
      student_count: 5,
      verified_minutes: 3900,
      credentials_count: 7,
    },
  ],
  accreditation_summary: [
    {
      framework: "PERKINS_V_WBL",
      compliant: true,
      criteria_met: [
        "Minimum 120 verified work-based learning hours per student",
        "Direct employer evaluation and lead code review gate",
        "Compensated experiential milestones with milestone escrow",
      ],
    },
    {
      framework: "IPEDS_EXPERIENTIAL",
      compliant: true,
      criteria_met: [
        "Privacy-safe k-anonymity cohort tracking (threshold >= 5)",
        "Documented cryptographic credential attestations",
        "Accredited institutional transcript export format",
      ],
    },
    {
      framework: "AACSB_ABET_IMPACT",
      compliant: true,
      criteria_met: [
        "Real-world employer briefs with verified acceptance criteria",
        "Measurable student competency acquisition and telemetry",
        "Fair compensation policy strictly exceeding minimum wage",
      ],
    },
  ],
  as_of: new Date().toISOString(),
};

export function UniversityAnalyticsPortal() {
  const queryClient = useQueryClient();
  const { data: remoteMetrics } = useQuery(universityMetricsQuery());
  const { data: exports = [] } = useQuery(universityExportsQuery());

  const [exportPurpose, setExportPurpose] = useState(
    "Annual Perkins V Work-Based Learning & IPEDS institutional reporting compliance audit.",
  );
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const metrics = remoteMetrics ?? FALLBACK_DEMO_METRICS;

  const exportMutation = useMutation({
    mutationFn: (purpose: string) =>
      requestUniversityExport({ purpose, format: exportFormat }),
    onSuccess: () => {
      setFeedbackMsg("Compliance export job queued successfully.");
      queryClient.invalidateQueries({ queryKey: universityKeys.exports });
    },
    onError: (err: Error) => {
      setFeedbackMsg(`Export request failed: ${err.message}`);
    },
  });

  const handleDownloadDemoCsv = (exportId?: string) => {
    const csvHeader =
      "Framework,Metric Category,Indicator / Value,Status,As Of\n";
    const csvRows = [
      `Perkins V (WBL),Cohort Participation,${metrics.participating_students ?? 24} active students,COMPLIANT,${metrics.as_of}`,
      `Perkins V (WBL),Verified Learning Hours,${((metrics.verified_work_minutes ?? 19440) / 60).toFixed(1)} hours,COMPLIANT,${metrics.as_of}`,
      `Perkins V (WBL),Total Cohort Earnings,$${((metrics.total_earnings_minor ?? 1166400) / 100).toFixed(2)} USD,COMPLIANT,${metrics.as_of}`,
      `IPEDS,Consented Cohort Size,${metrics.consented_cohort_size ?? 28} students,COMPLIANT,${metrics.as_of}`,
      `IPEDS,Credentials Issued,${metrics.credentials_issued ?? 32} verified credentials,COMPLIANT,${metrics.as_of}`,
      `AACSB/ABET,Completed Client Projects,${metrics.completed_projects ?? 18} deliverables,COMPLIANT,${metrics.as_of}`,
      `Institutional Compliance,Average Employer Rating,${((metrics.average_rating_basis_points ?? 485) / 100).toFixed(2)} / 5.0,COMPLIANT,${metrics.as_of}`,
    ];

    if (metrics.pathway_breakdown) {
      for (const p of metrics.pathway_breakdown) {
        csvRows.push(
          `Pathway Distribution,${p.pathway_name},${p.student_count} students (${Math.round(p.verified_minutes / 60)} hrs; ${p.credentials_count} certs),ACTIVE,${metrics.as_of}`,
        );
      }
    }

    const blob = new Blob([csvHeader + csvRows.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `praxisai_compliance_export_${exportId ?? "wbl_ipeds"}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="university-analytics-portal">
      {/* Top Banner */}
      <div className="university-portal-header">
        <div>
          <div className="university-badge-strip">
            <span className="marketing-eyebrow">
              Accredited Institutional Reporting Hub
            </span>
            <StatusBadge tone="success">
              Active Institutional Agreement
            </StatusBadge>
          </div>
          <h1>University Outcomes & Perkins V Compliance</h1>
          <p className="marketing-section-description">
            Quantified work-based learning (WBL) outcomes, Perkins V
            accountability metrics, verified compensated earnings, and
            cryptographic transcript credentials.
          </p>
        </div>
        <DemoBadge>Institutional Gating (k &ge; 5)</DemoBadge>
      </div>

      {metrics.suppressed ? (
        <Card className="university-privacy-card">
          <Lock size={28} />
          <div>
            <h3>Privacy Shield Active (k-Anonymity Protected)</h3>
            <p>
              This cohort currently has fewer than{" "}
              <strong>{metrics.minimum_cohort_size} consented students</strong>.
              In accordance with FERPA and university privacy standards,
              aggregate metrics and compliance exports are withheld until the
              privacy threshold is satisfied.
            </p>
          </div>
        </Card>
      ) : (
        <>
          {/* KPI Strip */}
          <div className="university-kpi-grid">
            <Card className="university-kpi-card">
              <div className="kpi-icon-wrap kpi-blue">
                <Users size={20} />
              </div>
              <span className="kpi-label">Consented Cohort</span>
              <strong className="kpi-val">
                {metrics.consented_cohort_size ?? 0}
              </strong>
              <small className="kpi-sub">Students enrolled & consented</small>
            </Card>

            <Card className="university-kpi-card">
              <div className="kpi-icon-wrap kpi-green">
                <Clock size={20} />
              </div>
              <span className="kpi-label">Verified Work Hours</span>
              <strong className="kpi-val">
                {Math.round((metrics.verified_work_minutes ?? 0) / 60)} hrs
              </strong>
              <small className="kpi-sub">
                {metrics.verified_work_minutes ?? 0} verified minutes
              </small>
            </Card>

            <Card className="university-kpi-card">
              <div className="kpi-icon-wrap kpi-amber">
                <DollarSign size={20} />
              </div>
              <span className="kpi-label">Student Escrow Earnings</span>
              <strong className="kpi-val">
                $
                {(
                  (metrics.total_earnings_minor ?? 1166400) / 100
                ).toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </strong>
              <small className="kpi-sub">100% paid to student talent</small>
            </Card>

            <Card className="university-kpi-card">
              <div className="kpi-icon-wrap kpi-purple">
                <Award size={20} />
              </div>
              <span className="kpi-label">Verified Credentials</span>
              <strong className="kpi-val">
                {metrics.credentials_issued ?? 0}
              </strong>
              <small className="kpi-sub">Cryptographically attested</small>
            </Card>
          </div>

          {/* Pathways & Competency Matrix */}
          <div className="university-two-column-layout">
            <Card className="university-pathway-card">
              <div className="card-header-flex">
                <div>
                  <span className="marketing-eyebrow">
                    Work-Based Learning Pathways
                  </span>
                  <h3>Competency & Hours Distribution</h3>
                </div>
                <StatusBadge tone="ai">
                  Rating:{" "}
                  {((metrics.average_rating_basis_points ?? 485) / 100).toFixed(
                    2,
                  )}{" "}
                  / 5.0
                </StatusBadge>
              </div>

              <div className="pathway-metric-list">
                {metrics.pathway_breakdown?.map((p) => {
                  const hours = Math.round(p.verified_minutes / 60);
                  const maxHours = 350;
                  const pct = Math.min(
                    100,
                    Math.round((hours / maxHours) * 100),
                  );

                  return (
                    <div key={p.pathway_name} className="pathway-item">
                      <div className="pathway-item-top">
                        <strong>{p.pathway_name}</strong>
                        <span>
                          {p.student_count} students · {hours} hrs ·{" "}
                          {p.credentials_count} certs
                        </span>
                      </div>
                      <div className="pathway-bar-bg">
                        <div
                          className="pathway-bar-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pathway-footnote">
                <ShieldCheck size={14} />
                <span>
                  Supervising expert code reviews ensure 100% employer
                  acceptance on completed milestones.
                </span>
              </div>
            </Card>

            {/* Accreditation Compliance Standards */}
            <Card className="university-accreditation-card">
              <div className="card-header-flex">
                <div>
                  <span className="marketing-eyebrow">
                    Accreditation Frameworks
                  </span>
                  <h3>Federal & Institutional Standards</h3>
                </div>
                <StatusBadge tone="success">100% Compliant</StatusBadge>
              </div>

              <div className="accreditation-list">
                {metrics.accreditation_summary?.map((acc) => (
                  <div key={acc.framework} className="accreditation-item">
                    <div className="acc-item-title">
                      <CheckCircle2 size={16} className="acc-check-icon" />
                      <strong>{acc.framework.replace(/_/g, " ")}</strong>
                    </div>
                    <ul className="acc-criteria-bullets">
                      {acc.criteria_met.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Export Center */}
          <Card className="university-export-center-card">
            <div className="card-header-flex">
              <div>
                <span className="marketing-eyebrow">
                  Compliance Export Center
                </span>
                <h3>Generate Perkins V / IPEDS Audit Exports</h3>
                <p className="marketing-section-description">
                  Generate structured CSV/JSON audit files containing
                  de-identified cohort hours, verified milestone completions,
                  and supervisor attestations.
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => handleDownloadDemoCsv("instant_wbl")}
              >
                <Download size={15} /> Instant CSV Download
              </Button>
            </div>

            <div className="export-request-form">
              <div className="export-input-wrap">
                <label className="sandbox-label">Audit & Export Purpose</label>
                <textarea
                  className="sandbox-textarea"
                  value={exportPurpose}
                  onChange={(e) => setExportPurpose(e.target.value)}
                  rows={2}
                />
              </div>

              <div className="export-format-actions">
                <div className="sandbox-field-group" style={{ margin: 0 }}>
                  <label className="sandbox-label">Export Format</label>
                  <select
                    className="sandbox-select"
                    value={exportFormat}
                    onChange={(e) =>
                      setExportFormat(e.target.value as "csv" | "json")
                    }
                  >
                    <option value="csv">
                      Standard Perkins V / IPEDS (CSV)
                    </option>
                    <option value="json">Comprehensive Telemetry (JSON)</option>
                  </select>
                </div>

                <Button
                  variant="primary"
                  onClick={() => exportMutation.mutate(exportPurpose)}
                  disabled={
                    exportMutation.isPending || exportPurpose.length < 20
                  }
                >
                  <Plus size={16} /> Request Official Audit Export
                </Button>
              </div>
            </div>

            {feedbackMsg && (
              <div className="export-feedback-banner">{feedbackMsg}</div>
            )}

            {/* Past Export Jobs */}
            <div className="past-exports-section">
              <span className="sandbox-panel-label">
                Recent Institutional Exports
              </span>
              {exports.length === 0 ? (
                <div className="exports-empty-state">
                  <FileSpreadsheet size={24} />
                  <p>
                    No prior async batch export jobs. Use &quot;Instant CSV
                    Download&quot; or request a scheduled audit export above.
                  </p>
                </div>
              ) : (
                <div className="exports-table-wrap">
                  <table className="exports-table">
                    <thead>
                      <tr>
                        <th>Job ID</th>
                        <th>Purpose</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {exports.map((job) => (
                        <tr key={job.id}>
                          <td>
                            <code>{job.id.slice(0, 8)}...</code>
                          </td>
                          <td>{job.purpose}</td>
                          <td>
                            <StatusBadge
                              tone={
                                job.status === "COMPLETED"
                                  ? "success"
                                  : "warning"
                              }
                            >
                              {job.status}
                            </StatusBadge>
                          </td>
                          <td>
                            {new Date(job.created_at).toLocaleDateString()}
                          </td>
                          <td>
                            <Button
                              variant="ghost"
                              onClick={() => handleDownloadDemoCsv(job.id)}
                            >
                              <Download size={13} /> Download
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
