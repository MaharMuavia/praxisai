"use client";

import { useId, useState } from "react";
import {
  Bot,
  DollarSign,
  Percent,
  ShieldCheck,
  TrendingUp,
  Users,
} from "lucide-react";
import { Card } from "@/components/ui";

export function UnitEconomicsCalculator() {
  const [projectVolume, setProjectVolume] = useState(10);
  const [avgProjectPrice, setAvgProjectPrice] = useState(4000);
  const [studentPayoutPct, setStudentPayoutPct] = useState(70);
  const [geminiCostPerProject, setGeminiCostPerProject] = useState(1.2);

  const volumeInputId = useId();
  const priceInputId = useId();
  const payoutInputId = useId();
  const geminiInputId = useId();

  // Computations
  const monthlyGmv = projectVolume * avgProjectPrice;
  const studentPayoutMonthly = Math.round(
    monthlyGmv * (studentPayoutPct / 100),
  );
  const studioGrossMargin = monthlyGmv - studentPayoutMonthly;
  const totalGeminiCostMonthly = Number(
    (projectVolume * geminiCostPerProject).toFixed(2),
  );
  const studioNetMargin = Number(
    (studioGrossMargin - totalGeminiCostMonthly).toFixed(2),
  );
  const studioMarginPct = ((studioNetMargin / monthlyGmv) * 100).toFixed(1);
  const aiCostPct = ((totalGeminiCostMonthly / monthlyGmv) * 100).toFixed(3);
  const annualGmvRunRate = monthlyGmv * 12;
  const annualStudentEarnings = studentPayoutMonthly * 12;

  return (
    <div className="unit-economics-calculator" style={{ marginTop: "2rem" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        {/* Controls Card */}
        <Card
          style={{
            padding: "1.75rem",
            background: "var(--card, #ffffff)",
            border: "1px solid var(--line, #e2e8f0)",
            borderRadius: "16px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              marginBottom: "1.25rem",
            }}
          >
            <div
              style={{
                background: "rgba(37, 99, 235, 0.1)",
                color: "var(--brand, #2563eb)",
                padding: "8px",
                borderRadius: "10px",
                display: "flex",
              }}
            >
              <TrendingUp size={20} />
            </div>
            <h3
              style={{
                margin: 0,
                fontSize: "1.25rem",
                fontWeight: 600,
                color: "var(--foreground, #0f172a)",
              }}
            >
              Economic Drivers
            </h3>
          </div>

          {/* Project Volume Slider */}
          <div style={{ marginBottom: "1.25rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <label
                htmlFor={volumeInputId}
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--text-secondary, #64748b)",
                }}
              >
                Monthly Bounded Projects
              </label>
              <strong style={{ color: "var(--brand, #2563eb)" }}>
                {projectVolume} projects
              </strong>
            </div>
            <input
              id={volumeInputId}
              type="range"
              min={1}
              max={50}
              step={1}
              value={projectVolume}
              onChange={(e) => setProjectVolume(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--brand, #2563eb)" }}
            />
          </div>

          {/* Average Project Value */}
          <div style={{ marginBottom: "1.25rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <label
                htmlFor={priceInputId}
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--text-secondary, #64748b)",
                }}
              >
                Average Project Price
              </label>
              <strong style={{ color: "var(--brand, #2563eb)" }}>
                ${avgProjectPrice.toLocaleString()} USD
              </strong>
            </div>
            <input
              id={priceInputId}
              type="range"
              min={1000}
              max={10000}
              step={500}
              value={avgProjectPrice}
              onChange={(e) => setAvgProjectPrice(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--brand, #2563eb)" }}
            />
          </div>

          {/* Student Squad Payout % */}
          <div style={{ marginBottom: "1.25rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <label
                htmlFor={payoutInputId}
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--text-secondary, #64748b)",
                }}
              >
                Student & Lead Squad Share
              </label>
              <strong style={{ color: "var(--success, #16a34a)" }}>
                {studentPayoutPct}%
              </strong>
            </div>
            <input
              id={payoutInputId}
              type="range"
              min={50}
              max={85}
              step={5}
              value={studentPayoutPct}
              onChange={(e) => setStudentPayoutPct(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--success, #16a34a)" }}
            />
          </div>

          {/* Gemini AI Cost per Project */}
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <label
                htmlFor={geminiInputId}
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--text-secondary, #64748b)",
                }}
              >
                Gemini 2.5 Inference Cost / Project
              </label>
              <strong style={{ color: "var(--accent, #9333ea)" }}>
                ${geminiCostPerProject.toFixed(2)} USD
              </strong>
            </div>
            <input
              id={geminiInputId}
              type="range"
              min={0.5}
              max={5.0}
              step={0.1}
              value={geminiCostPerProject}
              onChange={(e) => setGeminiCostPerProject(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent, #9333ea)" }}
            />
          </div>
        </Card>

        {/* Live Calculation Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
          }}
        >
          {/* Monthly GMV */}
          <Card
            style={{
              padding: "1.25rem",
              background: "var(--card, #ffffff)",
              border: "1px solid var(--line, #e2e8f0)",
              borderRadius: "14px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "var(--text-secondary, #64748b)",
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                }}
              >
                <DollarSign size={15} /> Monthly GMV
              </div>
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: "var(--foreground, #0f172a)",
                  marginTop: "0.5rem",
                }}
              >
                ${monthlyGmv.toLocaleString()}
              </div>
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              ${annualGmvRunRate.toLocaleString()} annualized run-rate
            </div>
          </Card>

          {/* Student Payout */}
          <Card
            style={{
              padding: "1.25rem",
              background: "rgba(22, 163, 74, 0.04)",
              border: "1px solid rgba(22, 163, 74, 0.2)",
              borderRadius: "14px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "var(--success, #16a34a)",
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                }}
              >
                <Users size={15} /> Student Earnings
              </div>
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: "var(--success, #16a34a)",
                  marginTop: "0.5rem",
                }}
              >
                ${studentPayoutMonthly.toLocaleString()}
              </div>
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              ${annualStudentEarnings.toLocaleString()}/yr paid to talent
            </div>
          </Card>

          {/* Studio Net Margin */}
          <Card
            style={{
              padding: "1.25rem",
              background: "rgba(37, 99, 235, 0.04)",
              border: "1px solid rgba(37, 99, 235, 0.2)",
              borderRadius: "14px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "var(--brand, #2563eb)",
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                }}
              >
                <Percent size={15} /> Studio Margin
              </div>
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: "var(--brand, #2563eb)",
                  marginTop: "0.5rem",
                }}
              >
                ${studioNetMargin.toLocaleString()}
              </div>
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              {studioMarginPct}% net operational take-rate
            </div>
          </Card>

          {/* Gemini AI Overhead */}
          <Card
            style={{
              padding: "1.25rem",
              background: "rgba(147, 51, 234, 0.04)",
              border: "1px solid rgba(147, 51, 234, 0.2)",
              borderRadius: "14px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "var(--accent, #9333ea)",
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                }}
              >
                <Bot size={15} /> Gemini Compute
              </div>
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: "var(--accent, #9333ea)",
                  marginTop: "0.5rem",
                }}
              >
                ${totalGeminiCostMonthly.toFixed(2)}
              </div>
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              {aiCostPct}% of GMV (high software margin)
            </div>
          </Card>
        </div>
      </div>

      {/* Escrow Ledger Flow Visualizer */}
      <Card
        style={{
          padding: "1.75rem",
          background: "var(--card, #ffffff)",
          border: "1px solid var(--line, #e2e8f0)",
          borderRadius: "16px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "1rem",
          }}
        >
          <div
            style={{
              background: "rgba(16, 185, 129, 0.1)",
              color: "var(--success, #10b981)",
              padding: "8px",
              borderRadius: "10px",
              display: "flex",
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <h3
              style={{
                margin: 0,
                fontSize: "1.15rem",
                fontWeight: 600,
                color: "var(--foreground, #0f172a)",
              }}
            >
              Double-Entry Escrow Ledger Architecture
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: "0.85rem",
                color: "var(--text-secondary, #64748b)",
              }}
            >
              Deterministic funding gates ensure zero counterparty risk for
              students and employers.
            </p>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            marginTop: "1.25rem",
          }}
        >
          <div
            style={{
              padding: "1rem",
              background: "var(--muted, #f8fafc)",
              borderRadius: "10px",
              border: "1px solid var(--line, #e2e8f0)",
            }}
          >
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary, #64748b)",
              }}
            >
              STEP 1: INTAKE & DEPOSIT
            </span>
            <div
              style={{
                fontWeight: 600,
                marginTop: "4px",
                color: "var(--foreground, #0f172a)",
              }}
            >
              100% Escrow Hold
            </div>
            <p
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
                margin: "4px 0 0 0",
              }}
            >
              Employer funds held in balanced suspense account before squad
              formation.
            </p>
          </div>

          <div
            style={{
              padding: "1rem",
              background: "var(--muted, #f8fafc)",
              borderRadius: "10px",
              border: "1px solid var(--line, #e2e8f0)",
            }}
          >
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary, #64748b)",
              }}
            >
              STEP 2: SUPERVISED SPRINT
            </span>
            <div
              style={{
                fontWeight: 600,
                marginTop: "4px",
                color: "var(--foreground, #0f172a)",
              }}
            >
              Milestone QA Gate
            </div>
            <p
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
                margin: "4px 0 0 0",
              }}
            >
              Gemini + Coordinator verify immutable deliverable hashes against
              criteria.
            </p>
          </div>

          <div
            style={{
              padding: "1rem",
              background: "rgba(22, 163, 74, 0.05)",
              borderRadius: "10px",
              border: "1px solid rgba(22, 163, 74, 0.2)",
            }}
          >
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--success, #16a34a)",
              }}
            >
              STEP 3: INSTANT SETTLEMENT
            </span>
            <div
              style={{
                fontWeight: 600,
                marginTop: "4px",
                color: "var(--success, #16a34a)",
              }}
            >
              Automatic Split Release
            </div>
            <p
              style={{
                fontSize: "0.8rem",
                color: "var(--text-secondary, #64748b)",
                margin: "4px 0 0 0",
              }}
            >
              70% released to student ledger, 30% retained by studio. Zero
              chargeback risk.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
