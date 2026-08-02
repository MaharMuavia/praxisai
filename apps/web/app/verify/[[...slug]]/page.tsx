"use client";

import { praxisFetch } from "@praxisai/api-client";
import { CheckCircle2, Search, ShieldAlert } from "lucide-react";
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
    if (initialSlug) void verify(initialSlug);
  }, [initialSlug]);

  return (
    <main className="content-page">
      <MarketingNav />
      <section className="content-hero">
        <div className="eyebrow">Public verification</div>
        <h1>Verify project evidence.</h1>
        <p>
          Check a PraxisAI credential without exposing private source code,
          client information, or unconsented portfolio evidence.
        </p>
      </section>
      <section className="content-body">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void verify(value);
          }}
          style={{ display: "flex", gap: 10, maxWidth: 720 }}
        >
          <label style={{ flex: 1 }}>
            <span className="sr-only">Credential ID or verification slug</span>
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Credential verification slug"
              style={{
                width: "100%",
                padding: 15,
                border: "1px solid var(--line)",
                borderRadius: 12,
              }}
            />
          </label>
          <button className="button button-primary" disabled={busy}>
            <Search size={16} /> {busy ? "Checking…" : "Verify"}
          </button>
        </form>
        {result && (
          <article className="panel" style={{ marginTop: 30, padding: 28 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              {result.status === "VALID" && result.signature_valid ? (
                <CheckCircle2 color="var(--success)" />
              ) : (
                <ShieldAlert color="var(--danger)" />
              )}
              <h2 style={{ margin: 0 }}>
                {result.status === "VALID" && result.signature_valid
                  ? "Valid signed credential"
                  : result.status === "REVOKED"
                    ? "Credential revoked"
                    : "Credential unavailable"}
              </h2>
            </div>
            {result.environment_label && (
              <p>
                <span className="demo-badge">
                  {result.environment_label} credential
                </span>
              </p>
            )}
            {result.credential && (
              <dl>
                {Object.entries(result.credential)
                  .filter(
                    ([key]) =>
                      ![
                        "public_artifact_references",
                        "key_identifier",
                      ].includes(key),
                  )
                  .map(([key, item]) => (
                    <div className="data-row" key={key}>
                      <dt>
                        <strong>{key.replaceAll("_", " ")}</strong>
                      </dt>
                      <dd>
                        {typeof item === "object"
                          ? JSON.stringify(item)
                          : String(item)}
                      </dd>
                    </div>
                  ))}
              </dl>
            )}
          </article>
        )}
      </section>
    </main>
  );
}
