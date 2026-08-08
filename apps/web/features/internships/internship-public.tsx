"use client";

import { useQuery } from "@tanstack/react-query";
import {
  createUserWithEmailAndPassword,
  sendEmailVerification,
} from "firebase/auth";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { Brand } from "@/components/brand";
import { Button, Card, StatusBadge } from "@/components/ui";
import { getFirebaseAuth } from "@/lib/firebase";
import {
  internshipFetch,
  programsQuery,
  type InternshipProgram,
} from "@/lib/queries/internships/shared";

type ProgramDetail = InternshipProgram & {
  cohorts: {
    id: string;
    name: string;
    slug: string;
    status: string;
    starts_at: string;
    ends_at: string;
    capacity: number;
    timezone: string;
  }[];
  tracks: {
    id: string;
    name: string;
    version_id: string;
    title: string;
    summary: string;
    skill_outcomes: string[];
  }[];
};

export function InternshipProgramList() {
  const query = useQuery(programsQuery());
  if (query.isLoading)
    return (
      <div className="internship-loading">Loading available programs…</div>
    );
  if (query.isError)
    return (
      <div className="internship-error" role="alert">
        Programs are temporarily unavailable.
      </div>
    );
  return (
    <main className="internship-public-page">
      <header className="internship-public-header">
        <Brand />
        <div>
          <span className="marketing-eyebrow">PraxisAI internships</span>
          <h1>Structured preparation for real technical delivery.</h1>
          <p>
            Learn in sequence, produce evidence, complete bounded projects, and
            receive human review. No paid provider is required for demo
            operation.
          </p>
        </div>
      </header>
      <section className="internship-public-grid">
        {query.data?.map((program) => (
          <Card key={program.id}>
            <div className="internship-assignment-header">
              <div>
                <span className="internship-unit-type">
                  {program.duration_weeks}-week program
                </span>
                <h2>{program.name}</h2>
              </div>
              <StatusBadge
                tone={program.status === "ACTIVE" ? "success" : "warning"}
              >
                {program.status.replaceAll("_", " ")}
              </StatusBadge>
            </div>
            <p>{program.public_description}</p>
            <div className="internship-program-facts">
              <span>{program.duration_weeks} weeks</span>
              <span>{program.default_timezone}</span>
              {program.is_demo ? <span>Demo data</span> : null}
            </div>
            <Button href={`/internships/${program.slug}`} variant="primary">
              View program
            </Button>
          </Card>
        ))}
      </section>
    </main>
  );
}

export function InternshipProgramPage({ slug }: { slug: string }) {
  const query = useQuery({
    queryKey: ["internship-program", slug],
    queryFn: () =>
      internshipFetch<ProgramDetail>(`/internships/programs/${slug}`),
  });
  if (query.isLoading)
    return <div className="internship-loading">Loading program brief…</div>;
  if (query.isError || !query.data)
    return (
      <div className="internship-error" role="alert">
        Program not found or unavailable.
      </div>
    );
  const program = query.data;
  return (
    <main className="internship-public-page">
      <header className="internship-public-header">
        <Brand />
        <Link className="internship-back-link" href="/internships">
          All programs
        </Link>
        <div>
          <span className="marketing-eyebrow">
            {program.duration_weeks}-week operating model
          </span>
          <h1>{program.name}</h1>
          <p>{program.public_description}</p>
        </div>
      </header>
      <section className="internship-public-detail">
        <Card>
          <span className="marketing-eyebrow">Program sequence</span>
          <h2>Learning → practical delivery → reviewed evidence</h2>
          <ol className="internship-program-sequence">
            <li>Foundations and shared technical practice</li>
            <li>Track-specific applied learning</li>
            <li>Guided project with explicit acceptance criteria</li>
            <li>Independent capstone and human completion review</li>
          </ol>
        </Card>
        <Card>
          <span className="marketing-eyebrow">Tracks</span>
          <h2>Choose a credible direction.</h2>
          <div className="internship-track-list">
            {program.tracks.map((track) => (
              <article key={track.version_id}>
                <h3>{track.name}</h3>
                <p>{track.summary}</p>
                <small>{track.skill_outcomes.join(" · ")}</small>
              </article>
            ))}
          </div>
        </Card>
      </section>
      <section className="internship-cohort-list">
        <h2>Available cohorts</h2>
        {program.cohorts.map((cohort) => (
          <Card key={cohort.id}>
            <div>
              <h3>{cohort.name}</h3>
              <p>
                {cohort.timezone} ·{" "}
                {new Date(cohort.starts_at).toLocaleDateString()}–
                {new Date(cohort.ends_at).toLocaleDateString()}
              </p>
            </div>
            <Button
              href={`/internships/${program.slug}/apply?program=${program.id}&cohort=${cohort.id}`}
              variant="primary"
            >
              Apply to cohort
            </Button>
          </Card>
        ))}
      </section>
    </main>
  );
}

export function StudentSignup() {
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const credential = await createUserWithEmailAndPassword(
        getFirebaseAuth(),
        email,
        password,
      );
      await sendEmailVerification(credential.user);
      setMessage(
        "Verification email sent. Confirm it, then return here to complete provisioning.",
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to create the account",
      );
    } finally {
      setBusy(false);
    }
  }
  async function provision() {
    setBusy(true);
    setError(null);
    try {
      const auth = getFirebaseAuth();
      const user = auth.currentUser;
      if (!user) throw new Error("Create an account first.");
      await user.reload();
      if (!user.emailVerified)
        throw new Error("Verify the Firebase email before continuing.");
      const token = await user.getIdToken(true);
      await internshipFetch(
        `/internships/programs/${params.get("program") ?? ""}/signup`,
        {
          method: "POST",
          body: JSON.stringify({
            id_token: token,
            cohort_id: params.get("cohort"),
            consent_version: "internship-1",
          }),
        },
      );
      window.location.replace("/student/internship/application");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to provision the student account",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="internship-auth-page">
      <Card>
        <Brand />
        <span className="marketing-eyebrow">Student signup</span>
        <h1>Create a verified student identity.</h1>
        <p>
          Firebase email verification is required before PraxisAI creates a
          user, student membership, profile, or application.
        </p>
        <form className="internship-auth-form" onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              minLength={8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <Button disabled={busy} type="submit">
            Send verification email
          </Button>
        </form>
        {message ? (
          <div className="success" role="status">
            {message}
          </div>
        ) : null}
        <Button disabled={busy} onClick={provision} variant="secondary">
          I verified my email — continue
        </Button>
        {error ? (
          <div className="error" role="alert">
            {error}
          </div>
        ) : null}
      </Card>
    </main>
  );
}
