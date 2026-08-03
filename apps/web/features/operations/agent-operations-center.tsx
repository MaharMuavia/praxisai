"use client";

import { useQuery } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Filter,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { DemoBadge, DemoNotice } from "@/components/demo-boundary";
import { withDemoFallback } from "@/lib/demo-data";
import { fetchQuery, retryTransientError } from "@/lib/queries/shared";

type AgentRun = components["schemas"]["AgentRunView"];
type RunResult = { data: AgentRun[]; isDemo: boolean };

const demoRuns: AgentRun[] = [
  {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    project_id: "33333333-3333-4333-8333-333333333333",
    agent_name: "scope_proposer",
    status: "COMPLETED",
    model_identifier: "fixture-ai",
    prompt_version: "scope-v3",
    input_snapshot_hash: "sha256:demo-brief-01",
    output: { proposal: "Bounded directory workflow" },
    validation_status: "VALIDATED",
    latency_ms: 842,
    retry_count: 0,
    usage: { input_tokens: 612, output_tokens: 184 },
    correlation_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    is_demo: true,
    created_at: "2026-08-01T08:12:00.000Z",
  },
  {
    id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    project_id: "33333333-3333-4333-8333-333333333333",
    agent_name: "plan_proposer",
    status: "COMPLETED",
    model_identifier: "fixture-ai",
    prompt_version: "plan-v2",
    input_snapshot_hash: "sha256:demo-scope-02",
    output: { milestones: 3 },
    validation_status: "VALIDATED",
    latency_ms: 1054,
    retry_count: 0,
    usage: { input_tokens: 488, output_tokens: 231 },
    correlation_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    is_demo: true,
    created_at: "2026-08-01T09:20:00.000Z",
  },
  {
    id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    project_id: "33333333-3333-4333-8333-333333333333",
    agent_name: "qa_reviewer",
    status: "AWAITING_REVIEW",
    model_identifier: "fixture-ai",
    prompt_version: "qa-v1",
    input_snapshot_hash: "sha256:demo-release-03",
    output: { findings: 3, blockers: 0 },
    validation_status: "PENDING_HUMAN_REVIEW",
    latency_ms: 1376,
    retry_count: 1,
    usage: { input_tokens: 901, output_tokens: 302 },
    correlation_id: "ffffffff-ffff-4fff-8fff-ffffffffffff",
    is_demo: true,
    created_at: "2026-08-01T10:14:00.000Z",
  },
  {
    id: "11111111-2222-4333-8444-555555555555",
    project_id: null,
    agent_name: "readiness_summary",
    status: "FAILED",
    model_identifier: "fixture-ai",
    prompt_version: "readiness-v1",
    input_snapshot_hash: "sha256:demo-readiness-04",
    output: null,
    validation_status: "NOT_VALIDATED",
    latency_ms: 331,
    retry_count: 2,
    usage: null,
    correlation_id: "66666666-7777-4888-8999-000000000000",
    is_demo: true,
    created_at: "2026-08-01T10:32:00.000Z",
  },
];

function statusTone(status: string) {
  if (status === "COMPLETED") return "success";
  if (status === "FAILED") return "critical";
  return "warning";
}

export function AgentOperationsCenter() {
  const query = useQuery<RunResult>({
    queryKey: ["agents", "runs", "operations-center"],
    queryFn: async ({ signal }) =>
      withDemoFallback(
        fetchQuery<AgentRun[]>("/ops/agent-runs", signal),
        demoRuns,
      ),
    retry: retryTransientError,
  });
  const runs = query.data?.data ?? [];
  const isDemo = query.data?.isDemo || runs.some((run) => run.is_demo);
  const completed = runs.filter((run) => run.status === "COMPLETED").length;
  const failed = runs.filter((run) => run.status === "FAILED").length;
  const review = runs.filter(
    (run) => run.validation_status !== "VALIDATED",
  ).length;

  return (
    <div className="agent-operations-center">
      {isDemo ? (
        <DemoNotice>
          Demo data · Fixture AI runs are shown when the explicit demo
          environment is enabled.
        </DemoNotice>
      ) : null}
      {query.isPending ? (
        <div className="skeleton" aria-label="Loading agent operations" />
      ) : null}
      {query.isError ? (
        <div className="error" role="alert">
          Agent runs could not be loaded. This view does not substitute fixture
          records outside the explicit demo environment.
        </div>
      ) : null}
      {!query.isPending && !query.isError ? (
        <>
          <div className="agent-ops-metrics">
            <div>
              <span>Total runs</span>
              <strong>{runs.length}</strong>
              <small>structured records</small>
            </div>
            <div>
              <span>Validated</span>
              <strong>{completed}</strong>
              <small>
                <CheckCircle2 size={14} /> completed proposals
              </small>
            </div>
            <div>
              <span>Human review</span>
              <strong>{review}</strong>
              <small>
                <Clock3 size={14} /> boundary still open
              </small>
            </div>
            <div>
              <span>Failed</span>
              <strong>{failed}</strong>
              <small>
                <AlertTriangle size={14} /> recovery required
              </small>
            </div>
          </div>
          <section className="agent-ops-panel panel">
            <div className="panel-header">
              <div>
                <h2>Structured agent evidence</h2>
                <p>
                  Proposal output, policy validation, and human boundary state.
                </p>
              </div>
              <span className="status-badge">
                <Filter size={13} /> All runs
              </span>
            </div>
            <div className="agent-ops-list">
              {runs.map((run) => (
                <article className="agent-ops-row" key={run.id}>
                  <div className="agent-ops-row-title">
                    <span
                      className={`agent-ops-status agent-ops-${statusTone(run.status)}`}
                      aria-label={run.status}
                    >
                      <Sparkles size={15} />
                    </span>
                    <div>
                      <strong>{run.agent_name.replaceAll("_", " ")}</strong>
                      <small>
                        {run.project_id
                          ? `Project ${run.project_id.slice(0, 8)}…`
                          : "Cross-project operation"}
                      </small>
                    </div>
                  </div>
                  <div>
                    <span className="agent-ops-label">Run state</span>
                    <strong>{run.status.replaceAll("_", " ")}</strong>
                  </div>
                  <div>
                    <span className="agent-ops-label">Validation</span>
                    <strong>
                      {run.validation_status.replaceAll("_", " ")}
                    </strong>
                  </div>
                  <div>
                    <span className="agent-ops-label">Model boundary</span>
                    <strong>
                      {run.is_demo ? (
                        <>
                          <DemoBadge>Fixture AI</DemoBadge>
                        </>
                      ) : (
                        (run.model_identifier ?? "Provider not named")
                      )}
                    </strong>
                  </div>
                  <div>
                    <span className="agent-ops-label">Audit</span>
                    <strong>{run.input_snapshot_hash.slice(0, 20)}…</strong>
                    <small>
                      {run.retry_count} retries · {run.latency_ms ?? "—"} ms
                    </small>
                  </div>
                </article>
              ))}
            </div>
          </section>
          <div className="agent-ops-boundary">
            <ShieldCheck size={18} />
            <span>
              <strong>Human authority remains explicit.</strong> Agent runs can
              propose and report. They cannot approve money, permissions,
              release, disputes, or credentials.
            </span>
          </div>
        </>
      ) : null}
    </div>
  );
}
