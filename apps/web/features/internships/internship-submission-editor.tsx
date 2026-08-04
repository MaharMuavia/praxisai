"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Button, Card, StatusBadge } from "@/components/ui";
import { internshipFetch } from "@/lib/queries/internships/shared";
import {
  finalizeInternshipSubmission,
  type SubmissionDraft,
} from "@/lib/queries/internships/submissions";

type SubmissionForm = {
  github_url: string;
  demo_url: string;
  readme: string;
  reflection: string;
  architecture_diagram: string;
  test_report: string;
};

const emptyForm: SubmissionForm = {
  github_url: "",
  demo_url: "",
  readme: "",
  reflection: "",
  architecture_diagram: "",
  test_report: "",
};

function toForm(submission: SubmissionDraft): SubmissionForm {
  return {
    ...emptyForm,
    github_url: submission.links.github_url ?? "",
    demo_url: submission.links.demo_url ?? "",
    readme: submission.text_fields.readme ?? "",
    reflection: submission.text_fields.reflection ?? "",
    architecture_diagram: submission.text_fields.architecture_diagram ?? "",
    test_report: submission.text_fields.test_report ?? "",
  };
}

export function InternshipSubmissionEditor({
  submissionId,
}: {
  submissionId: string;
}) {
  const queryClient = useQueryClient();
  const submission = useQuery({
    queryKey: ["internship", "submission", submissionId],
    queryFn: () =>
      internshipFetch<SubmissionDraft>(
        `/internships/me/submissions/${submissionId}`,
      ),
  });
  const [form, setForm] = useState<SubmissionForm | null>(null);
  const currentForm =
    form ?? (submission.data ? toForm(submission.data) : emptyForm);
  const save = useMutation({
    mutationFn: () =>
      internshipFetch<SubmissionDraft>(
        `/internships/me/submissions/${submissionId}`,
        {
          method: "PUT",
          body: JSON.stringify({
            version: submission.data?.version ?? 1,
            links: {
              github_url: currentForm.github_url,
              demo_url: currentForm.demo_url,
            },
            text_fields: {
              readme: currentForm.readme,
              reflection: currentForm.reflection,
              architecture_diagram: currentForm.architecture_diagram,
              test_report: currentForm.test_report,
            },
            artifact_upload_ids: submission.data?.artifact_upload_ids ?? [],
          }),
        },
      ),
    onSuccess: async (next) => {
      setForm(toForm(next));
      await queryClient.invalidateQueries({
        queryKey: ["internship", "submission", submissionId],
      });
    },
  });
  const finalize = useMutation({
    mutationFn: () =>
      finalizeInternshipSubmission(
        submissionId,
        { version: submission.data?.version ?? 1, confirm: true },
        crypto.randomUUID(),
      ),
    onSuccess: (next) => setForm(toForm(next)),
  });

  if (submission.isPending) return <p>Loading submission draft…</p>;
  if (submission.isError || !submission.data) {
    return (
      <p role="alert">
        This submission is unavailable or no longer belongs to you.
      </p>
    );
  }

  const update = (key: keyof SubmissionForm, value: string) =>
    setForm((previous) => ({ ...(previous ?? currentForm), [key]: value }));
  const immutable = submission.data.state !== "DRAFT";

  return (
    <section className="internship-section">
      <div className="internship-section-heading">
        <div>
          <span className="marketing-eyebrow">Submission workspace</span>
          <h1>Build a reviewable evidence package.</h1>
        </div>
        <StatusBadge tone={immutable ? "success" : "ai"}>
          {submission.data.state}
        </StatusBadge>
      </div>
      <Card>
        <div className="form-grid">
          {(
            [
              ["github_url", "GitHub repository URL"],
              ["demo_url", "Live demo URL"],
            ] as const
          ).map(([key, label]) => (
            <label className="form-field" key={key}>
              <span>{label}</span>
              <input
                value={currentForm[key]}
                onChange={(event) => update(key, event.target.value)}
                disabled={immutable}
                type="url"
              />
            </label>
          ))}
          {(
            [
              ["readme", "README / setup notes"],
              ["reflection", "Reflection and trade-offs"],
              ["architecture_diagram", "Architecture diagram link or notes"],
              ["test_report", "Test report and known limitations"],
            ] as const
          ).map(([key, label]) => (
            <label className="form-field form-field-wide" key={key}>
              <span>{label}</span>
              <textarea
                value={currentForm[key]}
                onChange={(event) => update(key, event.target.value)}
                disabled={immutable}
                rows={4}
              />
            </label>
          ))}
        </div>
        {!immutable ? (
          <div className="internship-actions">
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending}
              variant="secondary"
            >
              {save.isPending ? "Saving…" : "Save draft"}
            </Button>
            <Button
              onClick={() => finalize.mutate()}
              disabled={finalize.isPending}
            >
              {finalize.isPending ? "Finalizing…" : "Finalize submission"}
            </Button>
          </div>
        ) : (
          <p className="internship-muted">
            Finalized versions are immutable and remain available for review.
          </p>
        )}
        {save.isError || finalize.isError ? (
          <p className="form-error" role="alert">
            The server rejected this change. Refresh the page to reconcile the
            latest version.
          </p>
        ) : null}
      </Card>
    </section>
  );
}
