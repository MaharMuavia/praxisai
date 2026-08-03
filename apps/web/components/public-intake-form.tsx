"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { apiBase } from "../lib/api";

const intakeSchema = z
  .object({
    kind: z.enum(["company", "student", "expert_lead", "university"]),
    full_name: z.string().trim().min(2, "Enter your full name").max(160),
    email: z
      .string()
      .trim()
      .email("Enter a valid work or personal email")
      .max(320),
    country: z.string().trim().min(2, "Enter your country").max(80),
    organization: z.string().trim().max(200),
    summary: z.string().trim().min(20, "Add at least 20 characters").max(4_000),
    track: z.string().trim().max(120),
    availability: z.string().trim(),
    consent: z.boolean().refine((value) => value, "Consent is required"),
    honeypot: z.string().max(200),
  })
  .superRefine((value, context) => {
    if (value.kind === "company" && !value.organization) {
      context.addIssue({
        code: "custom",
        path: ["organization"],
        message: "Enter your company name",
      });
    }
    if (value.kind === "university" && !value.organization) {
      context.addIssue({
        code: "custom",
        path: ["organization"],
        message: "Enter your institution",
      });
    }
    if (
      (value.kind === "student" || value.kind === "expert_lead") &&
      !value.track
    ) {
      context.addIssue({
        code: "custom",
        path: ["track"],
        message: "Tell us your technical focus",
      });
    }
    if (
      (value.kind === "student" || value.kind === "expert_lead") &&
      !value.availability
    ) {
      context.addIssue({
        code: "custom",
        path: ["availability"],
        message: "Tell us your weekly availability",
      });
    }
  });

type IntakeForm = z.input<typeof intakeSchema>;

const defaults: IntakeForm = {
  kind: "company",
  full_name: "",
  email: "",
  country: "",
  organization: "",
  summary: "",
  track: "",
  availability: "",
  consent: false,
  honeypot: "",
};

const kindLabels = {
  company: "Company project",
  student: "Student application",
  expert_lead: "Expert lead inquiry",
  university: "University partnership",
} as const;

export function PublicIntakeForm() {
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors },
  } = useForm<IntakeForm>({ defaultValues: defaults });
  const kind = watch("kind");

  async function submit(values: IntakeForm) {
    setServerError(null);
    setSubmitted(null);
    const parsed = intakeSchema.safeParse(values);
    if (!parsed.success) {
      for (const issue of parsed.error.issues) {
        const field = issue.path[0];
        if (typeof field === "string")
          setError(field as keyof IntakeForm, { message: issue.message });
      }
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch(`${apiBase}/public/${parsed.data.kind}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({
          kind: parsed.data.kind,
          full_name: parsed.data.full_name,
          email: parsed.data.email,
          country: parsed.data.country,
          consent: parsed.data.consent,
          source: "website-contact",
          company_name:
            parsed.data.kind === "company"
              ? parsed.data.organization
              : undefined,
          institution:
            parsed.data.kind === "university"
              ? parsed.data.organization
              : undefined,
          business_problem:
            parsed.data.kind === "company" ? parsed.data.summary : undefined,
          intended_purpose:
            parsed.data.kind === "university" ? parsed.data.summary : undefined,
          experience_summary:
            parsed.data.kind === "student" ? parsed.data.summary : undefined,
          technical_specializations:
            parsed.data.kind === "expert_lead"
              ? parsed.data.summary
              : undefined,
          technical_track: parsed.data.track || undefined,
          weekly_availability: parsed.data.availability
            ? Number(parsed.data.availability)
            : undefined,
          honeypot: parsed.data.honeypot,
        }),
      });
      const body = (await response.json().catch(() => null)) as {
        error?: { message?: string; correlation_id?: string };
        correlation_id?: string;
      } | null;
      if (!response.ok) {
        const correlation =
          body?.error?.correlation_id ??
          response.headers.get("X-Correlation-ID");
        throw new Error(
          `${body?.error?.message ?? "Unable to submit this request"}${correlation ? ` (Support ID: ${correlation})` : ""}`,
        );
      }
      setSubmitted(
        `Received. Your ${kindLabels[parsed.data.kind].toLowerCase()} is now queued for human review. Support ID: ${body?.correlation_id ?? response.headers.get("X-Correlation-ID") ?? "available in your confirmation"}.`,
      );
    } catch (reason: unknown) {
      setServerError(
        reason instanceof Error
          ? reason.message
          : "Unable to submit this request",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const summaryLabel =
    kind === "company"
      ? "What business problem should the project address?"
      : kind === "university"
        ? "What partnership or privacy question should we understand?"
        : "Tell us about your experience and goals";
  const organizationLabel =
    kind === "company"
      ? "Company name"
      : kind === "university"
        ? "Institution"
        : "Organization or affiliation (optional)";

  return (
    <div className="public-intake-card">
      <div className="public-intake-heading">
        <span className="marketing-eyebrow">Supported intake</span>
        <h2>Start with enough context for a useful human response.</h2>
        <p>
          No automatic marketing messages are sent. A submission creates an
          internal review record only after the API confirms it.
        </p>
      </div>
      {submitted ? (
        <div className="success" role="status">
          {submitted}
        </div>
      ) : null}
      {serverError ? (
        <div className="error" role="alert">
          {serverError}
        </div>
      ) : null}
      <form
        className="public-intake-form"
        onSubmit={handleSubmit(submit)}
        noValidate
      >
        <label>
          I am contacting PraxisAI about
          <select {...register("kind")}>
            {Object.entries(kindLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          {errors.kind ? (
            <span className="field-error">{errors.kind.message}</span>
          ) : null}
        </label>
        <div className="public-intake-grid">
          <label>
            Full name
            <input {...register("full_name")} autoComplete="name" />
            {errors.full_name ? (
              <span className="field-error">{errors.full_name.message}</span>
            ) : null}
          </label>
          <label>
            Email
            <input {...register("email")} autoComplete="email" type="email" />
            {errors.email ? (
              <span className="field-error">{errors.email.message}</span>
            ) : null}
          </label>
          <label>
            Country
            <input {...register("country")} autoComplete="country-name" />
            {errors.country ? (
              <span className="field-error">{errors.country.message}</span>
            ) : null}
          </label>
          <label>
            {organizationLabel}
            <input {...register("organization")} />
            {errors.organization ? (
              <span className="field-error">{errors.organization.message}</span>
            ) : null}
          </label>
        </div>
        <label>
          {summaryLabel}
          <textarea {...register("summary")} rows={5} />
          {errors.summary ? (
            <span className="field-error">{errors.summary.message}</span>
          ) : null}
        </label>
        {kind === "student" || kind === "expert_lead" ? (
          <div className="public-intake-grid">
            <label>
              Technical focus
              <input {...register("track")} />
              {errors.track ? (
                <span className="field-error">{errors.track.message}</span>
              ) : null}
            </label>
            <label>
              Weekly availability (hours)
              <input
                {...register("availability")}
                inputMode="numeric"
                type="number"
                min="1"
                max="80"
              />
              {errors.availability ? (
                <span className="field-error">
                  {errors.availability.message}
                </span>
              ) : null}
            </label>
          </div>
        ) : null}
        <label className="public-intake-honeypot" aria-hidden="true">
          Website
          <input {...register("honeypot")} tabIndex={-1} autoComplete="off" />
        </label>
        <label className="public-intake-consent">
          <input {...register("consent")} type="checkbox" /> I agree that
          PraxisAI may use this information to review this request and contact
          me about the stated pathway. It will not be used for unrelated
          marketing.
          {errors.consent ? (
            <span className="field-error">{errors.consent.message}</span>
          ) : null}
        </label>
        <button
          className="ui-button ui-button-primary"
          disabled={submitting}
          type="submit"
        >
          {submitting ? "Submitting securely…" : "Submit for human review"}
        </button>
      </form>
    </div>
  );
}
