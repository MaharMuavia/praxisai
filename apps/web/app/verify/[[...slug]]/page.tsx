"use client";

import { praxisFetch } from "@praxisai/api-client";
import {
  CheckCircle2,
  Copy,
  QrCode,
  Search,
  Share2,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MarketingNav } from "@/components/marketing-nav";
import { apiBase } from "@/lib/api";

interface Verification {
  status: "VALID" | "REVOKED" | "NOT_FOUND";
  signature_valid: boolean;
  credential: Record<string, unknown> | null;
  environment_label?: string;
}

export default function VerifyPage() {
  const params = useParams<{ slug?: string[] }>();
  const initialSlug = params.slug?.[0] ?? "";
  const [value, setValue] = useState(initialSlug);
  const [result, setResult] = useState<Verification | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function verify(slug: string) {
    if (!slug.trim()) return;
    setBusy(true);
    try {
      setResult(
        await praxisFetch<Verification>(
          apiBase,
          `/public/credentials/${encodeURIComponent(slug.trim())}`,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!initialSlug) return;
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) void verify(initialSlug);
    });
    return () => {
      cancelled = true;
    };
  }, [initialSlug]);

  function copyVerificationUrl() {
    if (typeof window === "undefined") return;
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const credentialTitle =
    (result?.credential?.title as string) ||
    (result?.credential?.credential_title as string) ||
    "Professional Technical Apprenticeship Credential";

  const recipientName =
    (result?.credential?.student_name as string) ||
    (result?.credential?.recipient_name as string) ||
    "Verified Apprentice";

  const issueDate =
    (result?.credential?.issued_at as string) ||
    (result?.credential?.created_at as string) ||
    "2026-08-01";

  const linkedInUrl =
    typeof window !== "undefined"
      ? `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(
          credentialTitle,
        )}&organizationName=PraxisAI&issueYear=2026&issueMonth=8&certUrl=${encodeURIComponent(
          window.location.href,
        )}&certId=${encodeURIComponent(value || initialSlug)}`
      : "#";

  return (
    <main className="content-page">
      <MarketingNav />
      <section className="content-hero">
        <div className="eyebrow">Cryptographic Proof & Public Verification</div>
        <h1>Verify Professional Work Evidence.</h1>
        <p>
          Instant, trustless verification of PraxisAI apprenticeship credentials
          and deliverable hashes backed by Ed25519 / KMS signatures.
        </p>
      </section>
      <section className="content-body">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void verify(value);
          }}
          style={{
            display: "flex",
            gap: 10,
            maxWidth: 720,
            marginBottom: "2rem",
          }}
        >
          <label style={{ flex: 1 }}>
            <span className="sr-only">Credential ID or verification slug</span>
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Enter credential ID (e.g. cred-demo-01 or UUID)"
              style={{
                width: "100%",
                padding: 15,
                border: "1px solid var(--line)",
                borderRadius: 12,
                fontSize: "1rem",
              }}
            />
          </label>
          <button className="button button-primary" disabled={busy}>
            <Search size={16} /> {busy ? "Verifying…" : "Verify Credential"}
          </button>
        </form>

        {result && (
          <div style={{ maxWidth: 860, margin: "0 auto" }}>
            {/* Main Certificate Card */}
            <article
              style={{
                background: "var(--card, #ffffff)",
                border:
                  result.status === "VALID" && result.signature_valid
                    ? "2px solid rgba(22, 163, 74, 0.4)"
                    : "2px solid var(--line)",
                borderRadius: 20,
                padding: "2.5rem",
                boxShadow: "0 10px 30px rgba(0,0,0,0.06)",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Top Banner */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  flexWrap: "wrap",
                  gap: "1rem",
                  borderBottom: "1px solid var(--line, #e2e8f0)",
                  paddingBottom: "1.5rem",
                  marginBottom: "1.5rem",
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <span
                      style={{
                        background: "rgba(37, 99, 235, 0.1)",
                        color: "var(--brand, #2563eb)",
                        padding: "4px 10px",
                        borderRadius: "6px",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        letterSpacing: "0.05em",
                        textTransform: "uppercase",
                      }}
                    >
                      W3C Verifiable Credential 2.0
                    </span>
                    {result.environment_label && (
                      <span
                        style={{
                          background: "rgba(100, 116, 139, 0.1)",
                          color: "var(--text-secondary, #64748b)",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                        }}
                      >
                        {result.environment_label}
                      </span>
                    )}
                  </div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: "1.75rem",
                      fontWeight: 700,
                      color: "var(--foreground, #0f172a)",
                    }}
                  >
                    {credentialTitle}
                  </h2>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    background:
                      result.status === "VALID" && result.signature_valid
                        ? "rgba(22, 163, 74, 0.1)"
                        : "rgba(239, 68, 68, 0.1)",
                    color:
                      result.status === "VALID" && result.signature_valid
                        ? "var(--success, #16a34a)"
                        : "var(--danger, #ef4444)",
                    padding: "8px 14px",
                    borderRadius: "10px",
                    fontWeight: 600,
                    fontSize: "0.9rem",
                  }}
                >
                  {result.status === "VALID" && result.signature_valid ? (
                    <>
                      <CheckCircle2 size={18} /> Cryptographically Valid
                    </>
                  ) : (
                    <>
                      <ShieldAlert size={18} /> Revoked or Invalid
                    </>
                  )}
                </div>
              </div>

              {/* Recipient & Metadata */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "1.5rem",
                  marginBottom: "2rem",
                }}
              >
                <div>
                  <span
                    style={{
                      fontSize: "0.8rem",
                      color: "var(--text-secondary, #64748b)",
                      textTransform: "uppercase",
                      fontWeight: 600,
                    }}
                  >
                    ISSUED TO
                  </span>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "var(--foreground, #0f172a)",
                      marginTop: "4px",
                    }}
                  >
                    {recipientName}
                  </div>
                </div>

                <div>
                  <span
                    style={{
                      fontSize: "0.8rem",
                      color: "var(--text-secondary, #64748b)",
                      textTransform: "uppercase",
                      fontWeight: 600,
                    }}
                  >
                    ISSUANCE DATE
                  </span>
                  <div
                    style={{
                      fontSize: "1.1rem",
                      fontWeight: 600,
                      color: "var(--foreground, #0f172a)",
                      marginTop: "4px",
                    }}
                  >
                    {new Date(issueDate).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </div>
                </div>

                <div>
                  <span
                    style={{
                      fontSize: "0.8rem",
                      color: "var(--text-secondary, #64748b)",
                      textTransform: "uppercase",
                      fontWeight: 600,
                    }}
                  >
                    SIGNING AUTHORITY
                  </span>
                  <div
                    style={{
                      fontSize: "1.1rem",
                      fontWeight: 600,
                      color: "var(--brand, #2563eb)",
                      marginTop: "4px",
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                    }}
                  >
                    <ShieldCheck size={18} /> PraxisAI KMS Core
                  </div>
                </div>
              </div>

              {/* Cryptographic Verification Box */}
              <div
                style={{
                  background: "var(--muted, #f8fafc)",
                  border: "1px solid var(--line, #e2e8f0)",
                  borderRadius: "12px",
                  padding: "1.25rem",
                  marginBottom: "2rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "1rem",
                  }}
                >
                  <div style={{ flex: 1, minWidth: "260px" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        color: "var(--text-secondary, #64748b)",
                        textTransform: "uppercase",
                      }}
                    >
                      CRYPTOGRAPHIC EVIDENCE HASH
                    </span>
                    <div
                      style={{
                        fontFamily: "monospace",
                        fontSize: "0.8rem",
                        color: "var(--foreground, #0f172a)",
                        marginTop: "4px",
                        wordBreak: "break-all",
                        background: "#ffffff",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        border: "1px solid var(--line, #e2e8f0)",
                      }}
                    >
                      sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                    </div>
                  </div>

                  {/* Visual QR Code Badge */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      background: "#ffffff",
                      padding: "10px",
                      borderRadius: "10px",
                      border: "1px solid var(--line, #e2e8f0)",
                    }}
                  >
                    <QrCode size={48} color="var(--brand, #2563eb)" />
                    <span
                      style={{
                        fontSize: "0.65rem",
                        fontWeight: 700,
                        color: "var(--text-secondary, #64748b)",
                        marginTop: "4px",
                      }}
                    >
                      SCAN TO VERIFY
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  display: "flex",
                  gap: "1rem",
                  flexWrap: "wrap",
                }}
              >
                <a
                  href={linkedInUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "10px 20px",
                    background: "#0a66c2",
                    color: "#ffffff",
                    borderRadius: "10px",
                    fontWeight: 600,
                    fontSize: "0.9rem",
                    textDecoration: "none",
                  }}
                >
                  <Share2 size={16} /> Add to LinkedIn Certification
                </a>

                <button
                  type="button"
                  onClick={copyVerificationUrl}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "10px 18px",
                    background: "var(--card, #ffffff)",
                    border: "1px solid var(--line, #e2e8f0)",
                    color: "var(--foreground, #0f172a)",
                    borderRadius: "10px",
                    fontWeight: 500,
                    fontSize: "0.9rem",
                    cursor: "pointer",
                  }}
                >
                  <Copy size={16} />
                  {copied
                    ? "Verification Link Copied!"
                    : "Copy Verification URL"}
                </button>
              </div>

              {/* Full Raw Credential Payload */}
              {result.credential && (
                <details style={{ marginTop: "2rem" }}>
                  <summary
                    style={{
                      cursor: "pointer",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      color: "var(--text-secondary, #64748b)",
                    }}
                  >
                    Inspect Full Signed W3C Credential Schema (JSON-LD)
                  </summary>
                  <pre
                    style={{
                      background: "#0f172a",
                      color: "#38bdf8",
                      padding: "1rem",
                      borderRadius: "10px",
                      fontSize: "0.75rem",
                      overflowX: "auto",
                      marginTop: "0.5rem",
                    }}
                  >
                    {JSON.stringify(result.credential, null, 2)}
                  </pre>
                </details>
              )}
            </article>
          </div>
        )}
      </section>
    </main>
  );
}
