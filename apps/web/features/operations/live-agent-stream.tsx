"use client";

import { useState } from "react";
import type { components } from "@praxisai/api-client";
import { CheckCircle2, Cpu, ShieldCheck, Sparkles } from "lucide-react";
import { DemoBadge } from "@/components/demo-boundary";

type AgentRun = components["schemas"]["AgentRunView"];

/**
 * Gemini returns usage under `usage_metadata` keys (prompt_token_count,
 * candidates_token_count); fixture and seeded records use input_tokens /
 * output_tokens. Read both rather than assuming one provider's shape.
 */
function readTokens(usage: AgentRun["usage"]): {
  input: number | null;
  output: number | null;
} {
  if (!usage || typeof usage !== "object") return { input: null, output: null };
  const record = usage as Record<string, unknown>;
  const pick = (...keys: string[]): number | null => {
    for (const key of keys) {
      const value = record[key];
      if (typeof value === "number" && Number.isFinite(value)) return value;
    }
    return null;
  };
  return {
    input: pick("input_tokens", "prompt_token_count", "promptTokenCount"),
    output: pick(
      "output_tokens",
      "candidates_token_count",
      "candidatesTokenCount",
    ),
  };
}

function statusIcon(status: string) {
  if (status === "COMPLETED" || status === "SUCCEEDED") {
    return <CheckCircle2 size={16} color="var(--success, #16a34a)" />;
  }
  return (
    <div
      style={{
        width: 14,
        height: 14,
        borderRadius: "50%",
        border: "2px solid var(--line, #cbd5e1)",
      }}
    />
  );
}

export function LiveAgentStream({ runs }: { runs: AgentRun[] }) {
  const ordered = [...runs]
    .sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
    .slice(0, 6);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected =
    ordered.find((run) => run.id === selectedId) ?? ordered[0] ?? null;

  if (!selected) {
    return (
      <div className="live-agent-stream panel" style={panelStyle}>
        <Header />
        <p style={{ margin: 0, color: "var(--text-secondary, #64748b)" }}>
          No agent runs have been recorded yet. This panel renders only real
          rows from the <code>agent_runs</code> table — it does not display
          sample data.
        </p>
      </div>
    );
  }

  const tokens = readTokens(selected.usage);
  const isFixture =
    selected.provider === "fixture" ||
    selected.model_identifier === "fixture-ai";

  return (
    <div className="live-agent-stream panel" style={panelStyle}>
      <Header />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        {ordered.map((run) => {
          const runTokens = readTokens(run.usage);
          const isSelected = run.id === selected.id;
          return (
            <button
              key={run.id}
              type="button"
              onClick={() => setSelectedId(run.id)}
              aria-pressed={isSelected}
              style={{
                textAlign: "left",
                padding: "1rem",
                borderRadius: "12px",
                border: isSelected
                  ? "2px solid var(--brand, #2563eb)"
                  : "1px solid var(--line, #e2e8f0)",
                background: isSelected
                  ? "rgba(37, 99, 235, 0.04)"
                  : "var(--card, #ffffff)",
                cursor: "pointer",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "6px",
                }}
              >
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    color: "var(--text-secondary, #64748b)",
                  }}
                >
                  {run.status}
                </span>
                {statusIcon(run.status)}
              </div>
              <strong
                style={{
                  display: "block",
                  fontSize: "0.9rem",
                  color: "var(--foreground, #0f172a)",
                  marginBottom: "4px",
                }}
              >
                {run.agent_name}
              </strong>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "0.75rem",
                  color: "var(--text-secondary, #64748b)",
                }}
              >
                <Cpu size={13} />
                {run.latency_ms === null ? "no latency" : `${run.latency_ms}ms`}
                {runTokens.output === null ? "" : ` · ${runTokens.output} tok`}
              </div>
            </button>
          );
        })}
      </div>

      <div
        style={{
          background: "var(--muted, #f8fafc)",
          border: "1px solid var(--line, #e2e8f0)",
          borderRadius: "14px",
          padding: "1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "1rem",
            marginBottom: "1.25rem",
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "4px",
                flexWrap: "wrap",
              }}
            >
              <h4 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600 }}>
                {selected.agent_name}
              </h4>
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  background: "rgba(147, 51, 234, 0.1)",
                  color: "var(--accent, #9333ea)",
                  fontWeight: 600,
                }}
              >
                {selected.model_identifier ?? "no model recorded"}
              </span>
              {isFixture ? <DemoBadge>Fixture AI</DemoBadge> : null}
            </div>
            <p
              style={{
                margin: 0,
                fontSize: "0.85rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              prompt <code>{selected.prompt_version}</code> · provider{" "}
              <code>{selected.provider}</code> · validation{" "}
              <code>{selected.validation_status}</code>
            </p>
          </div>

          <dl style={metricRowStyle}>
            <Metric
              label="LATENCY"
              value={
                selected.latency_ms === null ? "—" : `${selected.latency_ms} ms`
              }
            />
            <Metric
              label="TOKENS IN/OUT"
              value={`${tokens.input ?? "—"} / ${tokens.output ?? "—"}`}
            />
            <Metric label="RETRIES" value={String(selected.retry_count ?? 0)} />
          </dl>
        </div>

        <div style={{ display: "grid", gap: "1rem" }}>
          <div>
            <span style={labelStyle}>Input snapshot hash (integrity bind)</span>
            <pre style={codeStyle}>{selected.input_snapshot_hash}</pre>
          </div>
          <div>
            <span style={{ ...labelStyle, color: "var(--brand, #2563eb)" }}>
              Recorded structured output
            </span>
            <pre style={{ ...codeStyle, color: "#38bdf8" }}>
              {selected.output === null
                ? "null — run did not produce validated output"
                : JSON.stringify(selected.output, null, 2)}
            </pre>
          </div>
        </div>

        <div
          style={{
            marginTop: "1rem",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "0.8rem",
            background: "rgba(37, 99, 235, 0.05)",
            border: "1px solid rgba(37, 99, 235, 0.2)",
            padding: "8px 12px",
            borderRadius: "8px",
            color: "var(--brand, #2563eb)",
          }}
        >
          <ShieldCheck size={16} />
          <span>
            <strong>Human boundary:</strong>{" "}
            {selected.human_approval_required
              ? "approval required — this proposal cannot mutate business state on its own"
              : "no approval required"}
            {" · "}
            {selected.executed_action_evidence.length === 0
              ? "no actions executed by the agent"
              : `${selected.executed_action_evidence.length} executed action(s) recorded`}
          </span>
        </div>
      </div>
    </div>
  );
}

function Header() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        marginBottom: "1.5rem",
      }}
    >
      <div
        style={{
          background: "rgba(147, 51, 234, 0.1)",
          color: "var(--accent, #9333ea)",
          padding: "10px",
          borderRadius: "12px",
          display: "flex",
        }}
      >
        <Sparkles size={22} />
      </div>
      <div>
        <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600 }}>
          Agent run inspector
        </h3>
        <p
          style={{
            margin: "4px 0 0 0",
            fontSize: "0.85rem",
            color: "var(--text-secondary, #64748b)",
          }}
        >
          Recorded model, latency, token usage, prompt version, and human
          boundary for each stored run. Values come from the{" "}
          <code>agent_runs</code> table.
        </p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt
        style={{
          fontSize: "0.7rem",
          color: "var(--text-secondary, #64748b)",
          margin: 0,
        }}
      >
        {label}
      </dt>
      <dd style={{ fontSize: "0.9rem", fontWeight: 600, margin: 0 }}>
        {value}
      </dd>
    </div>
  );
}

const panelStyle = {
  background: "var(--card, #ffffff)",
  border: "1px solid var(--line, #e2e8f0)",
  borderRadius: "16px",
  padding: "1.75rem",
  marginBottom: "2rem",
} as const;

const metricRowStyle = {
  display: "flex",
  gap: "1rem",
  background: "var(--card, #ffffff)",
  padding: "8px 14px",
  borderRadius: "10px",
  border: "1px solid var(--line, #e2e8f0)",
  margin: 0,
} as const;

const labelStyle = {
  fontSize: "0.75rem",
  fontWeight: 600,
  textTransform: "uppercase",
  color: "var(--text-secondary, #64748b)",
  display: "block",
  marginBottom: "4px",
} as const;

const codeStyle = {
  background: "#0f172a",
  color: "#e2e8f0",
  padding: "12px",
  borderRadius: "8px",
  fontSize: "0.75rem",
  overflowX: "auto",
  maxHeight: "180px",
  margin: 0,
} as const;
