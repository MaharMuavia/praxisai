"use client";

import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { apiBase } from "../lib/api";
import { parseApiError } from "../lib/queries/shared";

const intakeSchema = z
  .object({
    kind: z.enum(["company", "student", "expert_lead", "university"]),
    full_name: z.string().trim().min(2, "Enter your full name").max(160),
    email: z.string().trim().email("Enter a valid email").max(320),
    country: z.string().trim().min(2, "Enter your country").max(80),
    organization: z.string().trim().max(200),
    summary: z.string().trim().max(4_000),
    desired_result: z.string().trim().max(4_000),
    project_category: z.string().trim().max(80),
    target_timeline: z.string().trim().max(120),
    data_sensitivity: z.enum([
      "public",
      "internal",
      "confidential",
      "restricted",
    ]),
    track: z.string().trim().max(2_000),
    education_status: z.string().trim().max(120),
    availability: z.string().trim(),
    years_experience: z.string().trim(),
    rate_expectations: z.string().trim().max(500),
    profile_url: z.string().trim(),
    role: z.string().trim().max(120),
    cohort_context: z.string().trim().max(2_000),
    privacy_requirements: z.string().trim().max(4_000),
    consent: z.boolean().refine((value) => value, "Consent is required"),
    honeypot: z.string().max(200),
  })
  .superRefine((value, context) => {
    const required = (field: keyof typeof value, message: string, min = 2) => {
      const candidate = value[field];
      if (typeof candidate !== "string" || candidate.length < min) {
        context.addIssue({ code: "custom", path: [field], message });
      }
    };
    if (value.kind === "company") {
      required("organization", "Enter your company name");
      required("summary", "Describe the business problem (20+ characters)", 20);
      required(
        "desired_result",
        "Describe the desired result (10+ characters)",
        10,
      );
      required("project_category", "Enter a project category");
      required("target_timeline", "Enter a target timeline");
    }
    if (value.kind === "student") {
      required("education_status", "Tell us your education status");
      required("track", "Tell us your technical focus");
      required(
        "summary",
        "Add at least 20 characters about your experience",
        20,
      );
      if (
        !Number.isInteger(Number(value.availability)) ||
        Number(value.availability) < 1
      ) {
        context.addIssue({
          code: "custom",
          path: ["availability"],
          message: "Enter weekly hours (1–80)",
        });
      }
    }
    if (value.kind === "expert_lead") {
      required("track", "Tell us your technical specializations");
      required(
        "summary",
        "Add at least 20 characters about your experience",
        20,
      );
      if (
        !Number.isInteger(Number(value.availability)) ||
        Number(value.availability) < 1
      ) {
        context.addIssue({
          code: "custom",
          path: ["availability"],
          message: "Enter weekly hours (1–80)",
        });
      }
      if (
        !Number.isInteger(Number(value.years_experience)) ||
        Number(value.years_experience) < 1
      ) {
        context.addIssue({
          code: "custom",
          path: ["years_experience"],
          message: "Enter years of experience (1â€“70)",
        });
      }
      if (!/^https?:\/\/[^\s]+$/i.test(value.profile_url)) {
        context.addIssue({
          code: "custom",
          path: ["profile_url"],
          message: "Enter a public profile URL",
        });
      }
    }
    if (value.kind === "university") {
      required("organization", "Enter your institution");
      required("role", "Tell us your role");
      required(
        "summary",
        "Describe the partnership purpose (20+ characters)",
        20,
      );
      required("cohort_context", "Describe the cohort context");
      required(
        "privacy_requirements",
        "Describe privacy requirements (20+ characters)",
        20,
      );
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
  desired_result: "",
  project_category: "",
  target_timeline: "",
  data_sensitivity: "internal",
  track: "",
  education_status: "",
  availability: "",
  years_experience: "",
  rate_expectations: "",
  profile_url: "",
  role: "",
  cohort_context: "",
  privacy_requirements: "",
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
  const idempotencyKey = useRef(crypto.randomUUID());
  const {
    register,
    handleSubmit,
    watch,
    setError,
    setFocus,
    reset,
    formState: { errors },
  } = useForm<IntakeForm>({ defaultValues: defaults });
  // React Hook Form's watch API is intentionally external to React Compiler.
  // eslint-disable-next-line react-hooks/incompatible-library
  const kind = watch("kind");

  const onInvalid = (formErrors: typeof errors) => {
    const firstField = Object.keys(formErrors)[0] as
      | keyof IntakeForm
      | undefined;
    if (firstField) setFocus(firstField);
  };

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
    const value = parsed.data;
    const common = {
      kind: value.kind,
      full_name: value.full_name,
      email: value.email,
      country: value.country,
      consent: value.consent,
      source: "website-contact",
      honeypot: value.honeypot,
    };
    const body =
      value.kind === "company"
        ? {
            ...common,
            company_name: value.organization,
            business_problem: value.summary,
            desired_result: value.desired_result,
            project_category: value.project_category,
            target_timeline: value.target_timeline,
            data_sensitivity: value.data_sensitivity,
          }
        : value.kind === "student"
          ? {
              ...common,
              education_status: value.education_status,
              technical_track: value.track,
              weekly_availability: Number(value.availability),
              experience_summary: value.summary,
            }
          : value.kind === "expert_lead"
            ? {
                ...common,
                technical_specializations: value.track,
                years_experience: Number(value.years_experience),
                weekly_availability: Number(value.availability),
                profile_url: value.profile_url,
                experience_summary: value.summary,
                rate_expectations: value.rate_expectations || undefined,
              }
            : {
                ...common,
                institution: value.organization,
                role: value.role,
                intended_purpose: value.summary,
                cohort_context: value.cohort_context,
                privacy_requirements: value.privacy_requirements,
              };
    setSubmitting(true);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15_000);
    try {
      const response = await fetch(`${apiBase}/public/${value.kind}`, {
        method: "POST",
        credentials: "include",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey.current,
        },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const parsedError = await parseApiError(response);
        const message =
          parsedError.status === 409
            ? "This request conflicts with an existing submission. Reload the page or use a new request."
            : parsedError.status === 429
              ? "Too many submissions from this address. Please try again later."
              : parsedError.message;
        throw new Error(
          `${message}${parsedError.correlationId ? ` (Support ID: ${parsedError.correlationId})` : ""}`,
        );
      }
      const responseBody = (await response.json()) as {
        correlation_id?: string;
      };
      const correlation =
        responseBody.correlation_id ?? response.headers.get("X-Correlation-ID");
      setSubmitted(
        `Received. Your ${kindLabels[value.kind].toLowerCase()} is queued for human review. Support ID: ${correlation ?? "available in your confirmation"}.`,
      );
    } catch (reason: unknown) {
      setServerError(
        reason instanceof DOMException && reason.name === "AbortError"
          ? "The request timed out. Your form is still filled in; try again."
          : reason instanceof Error
            ? reason.message
            : "Unable to submit this request",
      );
    } finally {
      window.clearTimeout(timeout);
      setSubmitting(false);
    }
  }

  const summaryLabel =
    kind === "company"
      ? "What business problem should the project address?"
      : kind === "university"
        ? "What partnership purpose should we understand?"
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
      {Object.keys(errors).length ? (
        <div className="error" role="alert" tabIndex={-1}>
          <span id="intake-error-summary">
            Please correct the highlighted fields before submitting.
          </span>
        </div>
      ) : null}
      {submitted ? (
        <button
          className="ui-button ui-button-secondary"
          type="button"
          onClick={() => {
            reset(defaults);
            setSubmitted(null);
            setServerError(null);
            idempotencyKey.current = crypto.randomUUID();
          }}
        >
          Submit another request
        </button>
      ) : (
        <form
          className="public-intake-form"
          onSubmit={handleSubmit(submit, onInvalid)}
          noValidate
          aria-describedby={
            Object.keys(errors).length ? "intake-error-summary" : undefined
          }
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
                <span className="field-error">
                  {errors.organization.message}
                </span>
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
          {kind === "company" ? (
            <div className="public-intake-grid">
              <label>
                Desired result
                <input {...register("desired_result")} />
                {errors.desired_result ? (
                  <span className="field-error">
                    {errors.desired_result.message}
                  </span>
                ) : null}
              </label>
              <label>
                Project category
                <input {...register("project_category")} />
                {errors.project_category ? (
                  <span className="field-error">
                    {errors.project_category.message}
                  </span>
                ) : null}
              </label>
              <label>
                Target timeline
                <input {...register("target_timeline")} />
                {errors.target_timeline ? (
                  <span className="field-error">
                    {errors.target_timeline.message}
                  </span>
                ) : null}
              </label>
              <label>
                Data sensitivity
                <select {...register("data_sensitivity")}>
                  <option value="internal">Internal</option>
                  <option value="public">Public</option>
                  <option value="confidential">Confidential</option>
                  <option value="restricted">Restricted</option>
                </select>
              </label>
            </div>
          ) : null}
          {kind === "student" ? (
            <div className="public-intake-grid">
              <label>
                Education status
                <input {...register("education_status")} />
                {errors.education_status ? (
                  <span className="field-error">
                    {errors.education_status.message}
                  </span>
                ) : null}
              </label>
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
          {kind === "expert_lead" ? (
            <div className="public-intake-grid">
              <label>
                Technical specializations
                <input {...register("track")} />
                {errors.track ? (
                  <span className="field-error">{errors.track.message}</span>
                ) : null}
              </label>
              <label>
                Years of experience
                <input
                  {...register("years_experience")}
                  inputMode="numeric"
                  type="number"
                  min="1"
                  max="70"
                  aria-invalid={errors.years_experience ? "true" : "false"}
                  aria-describedby={
                    errors.years_experience
                      ? "years-experience-error"
                      : undefined
                  }
                />
                {errors.years_experience ? (
                  <span id="years-experience-error" className="field-error">
                    {errors.years_experience.message}
                  </span>
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
              <label>
                Public profile URL
                <input {...register("profile_url")} type="url" />
                {errors.profile_url ? (
                  <span className="field-error">
                    {errors.profile_url.message}
                  </span>
                ) : null}
              </label>
              <label>
                Rate expectations (optional)
                <input {...register("rate_expectations")} maxLength={500} />
              </label>
            </div>
          ) : null}
          {kind === "university" ? (
            <div className="public-intake-grid">
              <label>
                Your role
                <input {...register("role")} />
                {errors.role ? (
                  <span className="field-error">{errors.role.message}</span>
                ) : null}
              </label>
              <label>
                Cohort context
                <textarea {...register("cohort_context")} rows={3} />
                {errors.cohort_context ? (
                  <span className="field-error">
                    {errors.cohort_context.message}
                  </span>
                ) : null}
              </label>
              <label>
                Privacy requirements
                <textarea {...register("privacy_requirements")} rows={3} />
                {errors.privacy_requirements ? (
                  <span className="field-error">
                    {errors.privacy_requirements.message}
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
      )}
    </div>
  );
}
