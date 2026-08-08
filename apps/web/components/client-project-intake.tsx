"use client";

import { praxisFetch, type components } from "@praxisai/api-client";
import { ArrowLeft, ArrowRight, Save, Send } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { apiBase } from "../lib/api";
const draftKey = "praxisai:client-project-intake:v1";

const intakeSchema = z.object({
  title: z.string().trim().min(3, "Enter a project title").max(200),
  category: z.string().min(2, "Choose a supported project type"),
  desired_outcome: z
    .string()
    .trim()
    .min(10, "Describe the business outcome")
    .max(4000),
  target_users: z
    .string()
    .trim()
    .min(2, "Describe who will use the result")
    .max(2000),
  description: z
    .string()
    .trim()
    .min(20, "Provide at least 20 characters")
    .max(20000),
  deliverables_text: z.string().trim().min(3, "List at least one deliverable"),
  constraints_text: z.string().max(6000),
  desired_deadline: z.string(),
  budget_usd: z
    .string()
    .refine((value) => value === "" || /^\d+(\.\d{1,2})?$/.test(value), {
      message: "Use a positive USD amount with no more than two decimals",
    }),
  data_sensitivity: z.enum([
    "public",
    "internal",
    "confidential",
    "restricted",
  ]),
  attachment_references_text: z.string().max(5000),
});

type IntakeForm = z.infer<typeof intakeSchema>;
type Project = components["schemas"]["ProjectView"];

const defaults: IntakeForm = {
  title: "",
  category: "",
  desired_outcome: "",
  target_users: "",
  description: "",
  deliverables_text: "",
  constraints_text: "",
  desired_deadline: "",
  budget_usd: "",
  data_sensitivity: "internal",
  attachment_references_text: "",
};

const fieldsByStep: (keyof IntakeForm)[][] = [
  ["title", "category", "desired_outcome", "target_users"],
  ["description", "deliverables_text", "constraints_text"],
  [
    "desired_deadline",
    "budget_usd",
    "data_sensitivity",
    "attachment_references_text",
  ],
];

function lines(value: string, limit: number) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, limit);
}

export function ClientProjectIntake() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [draftRestored, setDraftRestored] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    watch,
    reset,
    getValues,
    setError,
    clearErrors,
    formState: { errors },
  } = useForm<IntakeForm>({ defaultValues: defaults });

  useEffect(() => {
    const saved = window.localStorage.getItem(draftKey);
    if (!saved) return;
    try {
      reset(intakeSchema.partial().parse(JSON.parse(saved)) as IntakeForm);
      setDraftRestored(true);
    } catch {
      window.localStorage.removeItem(draftKey);
    }
  }, [reset]);

  useEffect(() => {
    // React Hook Form's subscription API is intentionally external to React Compiler.
    // eslint-disable-next-line react-hooks/incompatible-library
    const subscription = watch((value) => {
      window.localStorage.setItem(draftKey, JSON.stringify(value));
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  function validateStep() {
    clearErrors();
    const result = intakeSchema.safeParse(getValues());
    if (result.success) return true;
    const activeFields = new Set(fieldsByStep[step]);
    let valid = true;
    for (const issue of result.error.issues) {
      const field = issue.path[0];
      if (
        typeof field === "string" &&
        activeFields.has(field as keyof IntakeForm)
      ) {
        setError(field as keyof IntakeForm, { message: issue.message });
        valid = false;
      }
    }
    return valid;
  }

  function nextStep() {
    if (validateStep()) setStep((current) => Math.min(current + 1, 2));
  }

  async function submit() {
    clearErrors();
    setSubmitError(null);
    const result = intakeSchema.safeParse(getValues());
    if (!result.success) {
      for (const issue of result.error.issues) {
        const field = issue.path[0];
        if (typeof field === "string") {
          setError(field as keyof IntakeForm, { message: issue.message });
        }
      }
      setSubmitError("Review the highlighted intake fields before submitting.");
      return;
    }
    const values = result.data;
    const attachmentReferences = lines(values.attachment_references_text, 10);
    for (const reference of attachmentReferences) {
      try {
        const parsed = new URL(reference);
        if (parsed.protocol !== "https:") throw new Error("HTTPS required");
      } catch {
        setError("attachment_references_text", {
          message: `Invalid attachment URL: ${reference}`,
        });
        return;
      }
    }
    setSubmitting(true);
    try {
      const project = await praxisFetch<Project>(apiBase, "/projects", {
        method: "POST",
        body: JSON.stringify({
          title: values.title,
          category: values.category,
          desired_outcome: values.desired_outcome,
          target_users: values.target_users,
          description: values.description,
          deliverables: lines(values.deliverables_text, 20),
          constraints: lines(values.constraints_text, 30),
          desired_deadline: values.desired_deadline || null,
          budget_guidance_minor: values.budget_usd
            ? Math.round(Number(values.budget_usd) * 100)
            : null,
          data_sensitivity: values.data_sensitivity,
          attachment_references: attachmentReferences,
        }),
      });
      window.localStorage.removeItem(draftKey);
      router.push(`/client/projects/${project.id}`);
    } catch (reason: unknown) {
      setSubmitError(
        reason instanceof Error
          ? reason.message
          : "Unable to create the project draft",
      );
      setSubmitting(false);
    }
  }

  const fieldError = (field: keyof IntakeForm) =>
    errors[field]?.message ? (
      <span className="field-error">{errors[field]?.message}</span>
    ) : null;

  return (
    <div className="intake">
      <div
        className="intake-progress"
        aria-label={`Intake step ${step + 1} of 3`}
      >
        {["Outcome", "Delivery", "Guardrails"].map((label, index) => (
          <span className={index <= step ? "active" : ""} key={label}>
            {index + 1}. {label}
          </span>
        ))}
      </div>
      {draftRestored && (
        <div className="success" role="status">
          Your locally saved draft was restored.
        </div>
      )}
      <form
        className="intake-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (step < 2) nextStep();
          else void submit();
        }}
      >
        {step === 0 && (
          <fieldset>
            <legend>Define the outcome</legend>
            <label>
              Project title
              <input {...register("title")} autoComplete="off" />
              {fieldError("title")}
            </label>
            <label>
              Project type
              <select {...register("category")}>
                <option value="">Select a supported type</option>
                <option value="informational_website">
                  Informational website
                </option>
                <option value="crud_tool">Small authenticated tool</option>
                <option value="dashboard">
                  Dashboard or reporting interface
                </option>
                <option value="data_analysis">Data cleaning or analysis</option>
                <option value="workflow_automation">Workflow automation</option>
                <option value="qa_accessibility">
                  QA or accessibility review
                </option>
                <option value="design_system">
                  UI/UX or design-system work
                </option>
              </select>
              {fieldError("category")}
            </label>
            <label>
              Desired business outcome
              <textarea {...register("desired_outcome")} rows={4} />
              {fieldError("desired_outcome")}
            </label>
            <label>
              Target users
              <textarea {...register("target_users")} rows={3} />
              {fieldError("target_users")}
            </label>
          </fieldset>
        )}
        {step === 1 && (
          <fieldset>
            <legend>Describe the delivery</legend>
            <label>
              Current problem and context
              <textarea {...register("description")} rows={6} />
              {fieldError("description")}
            </label>
            <label>
              Expected deliverables, one per line
              <textarea {...register("deliverables_text")} rows={5} />
              {fieldError("deliverables_text")}
            </label>
            <label>
              Constraints or dependencies, one per line
              <textarea {...register("constraints_text")} rows={5} />
              {fieldError("constraints_text")}
            </label>
          </fieldset>
        )}
        {step === 2 && (
          <fieldset>
            <legend>Confirm constraints and sensitivity</legend>
            <div className="form-grid">
              <label>
                Desired deadline
                <input {...register("desired_deadline")} type="date" />
                {fieldError("desired_deadline")}
              </label>
              <label>
                Budget guidance (USD, optional)
                <input
                  {...register("budget_usd")}
                  inputMode="decimal"
                  placeholder="2500"
                />
                {fieldError("budget_usd")}
              </label>
            </div>
            <label>
              Data sensitivity
              <select {...register("data_sensitivity")}>
                <option value="public">Public</option>
                <option value="internal">Internal</option>
                <option value="confidential">Confidential</option>
                <option value="restricted">
                  Restricted or highly sensitive
                </option>
              </select>
              {fieldError("data_sensitivity")}
              <small>
                Restricted data is routed to manual review and may be rejected
                from the pilot.
              </small>
            </label>
            <label>
              Existing brief links, one HTTPS URL per line
              <textarea {...register("attachment_references_text")} rows={4} />
              {fieldError("attachment_references_text")}
            </label>
            <div className="intake-review">
              <strong>Before submitting</strong>
              <p>
                This creates a draft only. AI may propose a scope, but a
                coordinator and you must approve the final scope and quote. Work
                cannot begin before verified funding.
              </p>
            </div>
          </fieldset>
        )}
        {submitError && <div className="error">{submitError}</div>}
        <div className="intake-actions">
          {step === 0 ? (
            <Link className="button button-ghost" href="/client/projects">
              <ArrowLeft size={16} /> Cancel
            </Link>
          ) : (
            <button
              className="button button-ghost"
              onClick={() => setStep((current) => current - 1)}
              type="button"
            >
              <ArrowLeft size={16} /> Back
            </button>
          )}
          <span className="draft-state">
            <Save size={15} /> Saved on this device
          </span>
          <button
            className="button button-primary"
            disabled={submitting}
            type="submit"
          >
            {step < 2 ? (
              <>
                Continue <ArrowRight size={16} />
              </>
            ) : (
              <>
                {submitting ? "Creating draft…" : "Create project draft"}{" "}
                <Send size={16} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
