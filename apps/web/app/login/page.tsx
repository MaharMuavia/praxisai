"use client";

import { praxisFetch } from "@praxisai/api-client";
import { ArrowRight, Lock, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Brand } from "@/components/brand";
import { apiBase } from "@/lib/api";
import { getSupabaseClient } from "@/lib/supabase";

interface DemoUser {
  user_id: string;
  display_name: string;
  organization_id: string;
  organization_name: string;
  role: string;
}

interface SessionView {
  user_id: string;
  display_name: string;
  email: string;
  active_membership: {
    organization_id: string;
    organization_name: string;
    role: string;
  };
}

function destination(role: string) {
  if (role === "student") return "/student";
  if (role === "technical_lead") return "/lead";
  if (role === "coordinator") return "/ops";
  if (role === "platform_admin") return "/admin";
  if (role === "university_viewer") return "/university";
  return "/client";
}

export default function LoginPage() {
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [selected, setSelected] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [useSupabase, setUseSupabase] = useState(
    Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL),
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    praxisFetch<DemoUser[]>(apiBase, "/auth/demo-users")
      .then((items) => {
        setUsers(items);
        if (items.length > 0) {
          setSelected(
            items[0].user_id +
              ":" +
              items[0].organization_id +
              ":" +
              items[0].role,
          );
        }
      })
      .catch(() => {
        // Demo users API unavailable in production mode
        setUseSupabase(true);
      });
  }, []);

  async function signInLocal() {
    const [user_id, organization_id, role] = selected.split(":");
    if (!user_id || !organization_id || !role) return;
    setBusy(true);
    setError(null);
    try {
      await praxisFetch<void>(apiBase, "/auth/local/session", {
        method: "POST",
        body: JSON.stringify({ user_id, organization_id, role }),
      });
      window.location.assign(destination(role));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in");
      setBusy(false);
    }
  }

  async function signInSupabase() {
    if (!email || !password) return;
    setBusy(true);
    setError(null);
    try {
      const { data, error: signInError } =
        await getSupabaseClient().auth.signInWithPassword({
          email,
          password,
        });
      if (signInError) throw signInError;
      const idToken = data.session?.access_token;
      if (!idToken) {
        throw new Error("Supabase did not return a verified session");
      }

      // Exchange the Supabase access token for the API's secure HttpOnly session.
      await praxisFetch<void>(apiBase, "/auth/session", {
        method: "POST",
        body: JSON.stringify({ access_token: idToken }),
      });

      // Retrieve server session to get verified role
      const me = await praxisFetch<SessionView>(apiBase, "/auth/me");
      window.location.assign(destination(me.active_membership.role));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Supabase authentication failed",
      );
      setBusy(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "var(--ink)",
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
    >
      <section
        className="operations-card"
        style={{ width: "min(520px, 100%)", transform: "none" }}
      >
        <Brand />
        <div style={{ marginTop: 40 }}>
          <span className="demo-badge">
            {useSupabase ? "Production Auth" : "Demo Environment"}
          </span>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 42,
              letterSpacing: "-.04em",
              marginBottom: 10,
            }}
          >
            {useSupabase ? "Sign in to PraxisAI" : "Enter a pilot workspace"}
          </h1>
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {useSupabase
              ? "Authenticate with your Supabase identity credentials."
              : "Choose a fictional user to inspect each role."}
          </p>
        </div>

        {useSupabase ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              signInSupabase();
            }}
            style={{ display: "grid", gap: 16, margin: "28px 0" }}
          >
            <label style={{ display: "grid", gap: 8, fontWeight: 700 }}>
              Email Address
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                required
                style={{
                  padding: 14,
                  borderRadius: 10,
                  border: "1px solid var(--line)",
                  background: "white",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: 8, fontWeight: 700 }}>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  padding: 14,
                  borderRadius: 10,
                  border: "1px solid var(--line)",
                  background: "white",
                }}
              />
            </label>
            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
            <button
              type="submit"
              className="button button-accent"
              style={{ width: "100%", marginTop: 8 }}
              disabled={busy || !email || !password}
            >
              {busy ? "Authenticating…" : "Sign In"} <Lock size={17} />
            </button>
          </form>
        ) : (
          <div style={{ margin: "28px 0" }}>
            <label
              style={{
                display: "grid",
                gap: 8,
                fontWeight: 700,
                marginBottom: 16,
              }}
            >
              Demo Identity
              <select
                value={selected}
                onChange={(event) => setSelected(event.target.value)}
                style={{
                  padding: 14,
                  borderRadius: 10,
                  border: "1px solid var(--line)",
                  background: "white",
                }}
              >
                {users.map((user) => (
                  <option
                    key={`${user.user_id}-${user.organization_id}-${user.role}`}
                    value={`${user.user_id}:${user.organization_id}:${user.role}`}
                  >
                    {user.display_name} · {user.role.replaceAll("_", " ")} ·{" "}
                    {user.organization_name}
                  </option>
                ))}
              </select>
            </label>
            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
            <button
              className="button button-accent"
              style={{ width: "100%", marginTop: 16 }}
              onClick={signInLocal}
              disabled={busy || !selected}
            >
              {busy ? "Opening workspace…" : "Continue"}{" "}
              <ArrowRight size={17} />
            </button>
          </div>
        )}

        <p
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: "var(--muted)",
            fontSize: 12,
            marginTop: 20,
          }}
        >
          <ShieldCheck size={15} /> All authentication sessions are verified
          server-side.
        </p>
      </section>
    </main>
  );
}
