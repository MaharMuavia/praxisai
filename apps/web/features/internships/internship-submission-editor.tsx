"use client";

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Card, StatusBadge } from "@/components/ui";
import {
  assignmentQuery,
  type InternshipAssignment,
} from "@/lib/queries/internships/assignments";
import {
  finalizeInternshipSubmission,
  getInternshipSubmission,
  requestSubmissionAIReview,
  type SubmissionAIReviewResponse,
  type SubmissionDraft,
  updateInternshipSubmission,
} from "@/lib/queries/internships/submissions";
import {
  getInternshipUpload,
  type InternshipUpload,
  internshipUploadKey,
  uploadInternshipArtifact,
} from "@/lib/queries/internships/uploads";

type ArtifactRequirement =
  InternshipAssignment["required_artifact_types"][number];
type ArtifactKind = "link" | "text" | "file";

const linkArtifactTypes = new Set(["github_url", "demo_url"]);
const textArtifactTypes = new Set([
  "readme",
  "reflection",
  "architecture_diagram",
  "test_report",
  "technical_report",
  "evaluation_plan",
]);
const friendlyLabels: Readonly<Record<string, string>> = {
  github_url: "GitHub repository URL",
  demo_url: "Live demo URL",
  readme: "README / setup notes",
  reflection: "Reflection and trade-offs",
  architecture_diagram: "Architecture diagram link or notes",
  test_report: "Test report and known limitations",
  technical_report: "Technical report",
  evaluation_plan: "Evaluation plan",
};
const pendingUploadStates = new Set(["INITIATED", "UPLOADED", "QUARANTINED"]);
const rejectedUploadStates = new Set([
  "REJECTED",
  "REJECTED_CLEANUP_PENDING",
  "EXPIRED",
  "EXPIRED_CLEANUP_PENDING",
]);

function artifactKind(type: string): ArtifactKind {
  if (linkArtifactTypes.has(type)) return "link";
  if (textArtifactTypes.has(type)) return "text";
  return "file";
}

function artifactLabel(type: string): string {
  return friendlyLabels[type] ?? type.replaceAll("_", " ");
}

function requirementLabel(requirement: ArtifactRequirement): string {
  return `${artifactLabel(requirement.type)}${requirement.required ? " (required)" : " (optional)"}`;
}

function toEditableValues(submission: SubmissionDraft): Record<string, string> {
  return { ...submission.links, ...submission.text_fields };
}

function splitEditableValues(
  requirements: ArtifactRequirement[],
  values: Record<string, string>,
): Pick<SubmissionDraft, "links" | "text_fields"> {
  const links: Record<string, string> = {};
  const textFields: Record<string, string> = {};
  for (const requirement of requirements) {
    const value = values[requirement.type]?.trim() ?? "";
    if (artifactKind(requirement.type) === "link") {
      if (value) links[requirement.type] = value;
    } else if (artifactKind(requirement.type) === "text") {
      if (value) textFields[requirement.type] = value;
    }
  }
  return { links, text_fields: textFields };
}

function uploadTone(state: string): "neutral" | "success" | "warning" {
  if (state === "CLEAN") return "success";
  if (rejectedUploadStates.has(state)) return "warning";
  return "neutral";
}

function uploadStatusMessage(upload: InternshipUpload): string {
  if (upload.state === "CLEAN")
    return `${upload.filename} is clean and ready to attach.`;
  if (upload.state === "QUARANTINED") {
    return `${upload.filename} is quarantined while malware scanning completes.`;
  }
  if (rejectedUploadStates.has(upload.state)) {
    return `${upload.filename} was rejected. Select a safe replacement file and retry.`;
  }
  return `${upload.filename}: ${upload.state.replaceAll("_", " ").toLowerCase()}.`;
}

export function InternshipSubmissionEditor({
  submissionId,
}: {
  submissionId: string;
}) {
  const queryClient = useQueryClient();
  const submissionKey = useMemo(
    () => ["internship", "submission", submissionId] as const,
    [submissionId],
  );
  const submission = useQuery({
    queryKey: submissionKey,
    queryFn: () => getInternshipSubmission(submissionId),
  });
  const assignment = useQuery(
    assignmentQuery(submission.data?.student_assignment_id ?? ""),
  );
  const [values, setValues] = useState<Record<string, string> | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<
    Record<string, File | undefined>
  >({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const lastHydratedSubmission = useRef<string | null>(null);

  useEffect(() => {
    if (!submission.data) return;
    if (lastHydratedSubmission.current !== submission.data.id) {
      setValues(toEditableValues(submission.data));
      lastHydratedSubmission.current = submission.data.id;
    }
  }, [submission.data]);

  const uploadIds = submission.data?.artifact_upload_ids ?? [];
  const uploadQueries = useQueries({
    queries: uploadIds.map((uploadId) => ({
      queryKey: internshipUploadKey(uploadId),
      queryFn: () => getInternshipUpload(uploadId),
      refetchInterval: (query: { state: { data?: InternshipUpload } }) => {
        const current = query.state.data;
        return current &&
          pendingUploadStates.has(current.state) &&
          Date.parse(current.expires_at) > Date.now()
          ? 2_000
          : false;
      },
      refetchIntervalInBackground: false,
      staleTime: 1_000,
    })),
  });
  const uploads = uploadQueries.flatMap((query) =>
    query.data ? [query.data] : [],
  );
  const uploadsByType = new Map<string, InternshipUpload[]>();
  for (const upload of uploads) {
    const current = uploadsByType.get(upload.artifact_type) ?? [];
    current.push(upload);
    uploadsByType.set(upload.artifact_type, current);
  }

  const requirements = assignment.data?.required_artifact_types ?? [];
  const currentValues =
    values ?? (submission.data ? toEditableValues(submission.data) : {});
  const immutable = submission.data?.state !== "DRAFT";
  const requiredArtifactsReady = requirements.every((requirement) => {
    if (!requirement.required) return true;
    if (artifactKind(requirement.type) !== "file") {
      return Boolean(currentValues[requirement.type]?.trim());
    }
    return (uploadsByType.get(requirement.type) ?? []).some(
      (upload) => upload.state === "CLEAN",
    );
  });
  const allAttachedUploadsClean =
    uploads.length === uploadIds.length &&
    uploads.every((attachedUpload) => attachedUpload.state === "CLEAN");
  const uploadStatusesLoaded = uploadQueries.every(
    (query) => !query.isPending && !query.isError,
  );

  const save = useMutation({
    mutationFn: () => {
      if (!submission.data || !assignment.data)
        throw new Error("Submission is unavailable.");
      const fields = splitEditableValues(requirements, currentValues);
      return updateInternshipSubmission(submissionId, {
        expected_version: submission.data.version,
        ...fields,
        artifact_upload_ids: submission.data.artifact_upload_ids,
      });
    },
    onSuccess: (next) => {
      queryClient.setQueryData(submissionKey, next);
      setValues(toEditableValues(next));
    },
  });

  const persistUpload = async (
    upload: InternshipUpload,
  ): Promise<SubmissionDraft> => {
    const current = queryClient.getQueryData<SubmissionDraft>(submissionKey);
    if (!current) throw new Error("Submission is unavailable.");
    const replacedUploadIds = current.artifact_upload_ids.filter((uploadId) => {
      const existing = queryClient.getQueryData<InternshipUpload>(
        internshipUploadKey(uploadId),
      );
      return existing?.artifact_type !== upload.artifact_type;
    });
    const next = await updateInternshipSubmission(submissionId, {
      expected_version: current.version,
      links: current.links,
      text_fields: current.text_fields,
      artifact_upload_ids: Array.from(
        new Set([...replacedUploadIds, upload.upload_id]),
      ),
    });
    queryClient.setQueryData(submissionKey, next);
    queryClient.setQueryData(internshipUploadKey(upload.upload_id), upload);
    return next;
  };

  const upload = useMutation({
    mutationFn: async ({ type, file }: { type: string; file: File }) => {
      if (!submission.data) throw new Error("Submission is unavailable.");
      const completed = await uploadInternshipArtifact(
        submission.data.student_assignment_id,
        type,
        file,
      );
      await persistUpload(completed);
      return completed;
    },
    onMutate: () => setUploadError(null),
    onSuccess: (completed) => {
      setSelectedFiles((previous) => ({
        ...previous,
        [completed.artifact_type]: undefined,
      }));
    },
    onError: (error) =>
      setUploadError(error instanceof Error ? error.message : "Upload failed."),
  });

  const finalize = useMutation({
    mutationFn: async () => {
      if (!submission.data || !assignment.data) {
        throw new Error("Submission is unavailable.");
      }
      const fields = splitEditableValues(requirements, currentValues);
      const saved = await updateInternshipSubmission(submissionId, {
        expected_version: submission.data.version,
        ...fields,
        artifact_upload_ids: submission.data.artifact_upload_ids,
      });
      queryClient.setQueryData(submissionKey, saved);
      return finalizeInternshipSubmission(
        submissionId,
        { version: saved.version, confirm: true },
        crypto.randomUUID(),
      );
    },
    onSuccess: (next) => {
      queryClient.setQueryData(submissionKey, next);
      setValues(toEditableValues(next));
    },
  });

  const [aiReview, setAiReview] = useState<SubmissionAIReviewResponse | null>(
    null,
  );
  const [aiReviewError, setAiReviewError] = useState<string | null>(null);

  const runAiReview = useMutation({
    mutationFn: async () => {
      setAiReviewError(null);
      return requestSubmissionAIReview(submissionId, [
        "Visual hierarchy and layout",
        "Responsive interface and color contrast",
        "Functional criteria satisfaction",
      ]);
    },
    onSuccess: (result) => {
      setAiReview(result);
    },
    onError: (error) => {
      setAiReviewError(
        error instanceof Error ? error.message : "Multimodal AI review failed.",
      );
    },
  });

  if (submission.isPending) return <p>Loading submission draft...</p>;
  if (submission.isError || !submission.data) {
    return (
      <p role="alert">
        This submission is unavailable or no longer belongs to you.
      </p>
    );
  }
  if (assignment.isPending) return <p>Loading assignment requirements...</p>;
  if (assignment.isError || !assignment.data) {
    return <p role="alert">The assignment requirements could not be loaded.</p>;
  }

  const update = (key: string, value: string) =>
    setValues((previous) => ({ ...(previous ?? currentValues), [key]: value }));

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
        <div className="form-grid internship-submission-form">
          {requirements.map((requirement) => {
            const kind = artifactKind(requirement.type);
            const label = requirementLabel(requirement);
            if (kind === "link") {
              return (
                <label className="form-field" key={requirement.type}>
                  <span>{label}</span>
                  <input
                    value={currentValues[requirement.type] ?? ""}
                    onChange={(event) =>
                      update(requirement.type, event.target.value)
                    }
                    disabled={immutable}
                    required={requirement.required}
                    type="url"
                  />
                </label>
              );
            }
            if (kind === "text") {
              return (
                <label
                  className="form-field form-field-wide"
                  key={requirement.type}
                >
                  <span>{label}</span>
                  <textarea
                    value={currentValues[requirement.type] ?? ""}
                    onChange={(event) =>
                      update(requirement.type, event.target.value)
                    }
                    disabled={immutable}
                    required={requirement.required}
                    rows={4}
                  />
                </label>
              );
            }
            const artifactUploads = uploadsByType.get(requirement.type) ?? [];
            const selectedFile = selectedFiles[requirement.type];
            return (
              <fieldset
                className="form-field form-field-wide internship-upload-field"
                key={requirement.type}
              >
                <legend>{label}</legend>
                {!immutable ? (
                  <div className="internship-upload-controls">
                    <input
                      aria-label={label}
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp,.zip,.ipynb,.json,.md,.txt"
                      onChange={(event) =>
                        setSelectedFiles((previous) => ({
                          ...previous,
                          [requirement.type]: event.target.files?.[0],
                        }))
                      }
                    />
                    <Button
                      variant="secondary"
                      disabled={
                        !selectedFile ||
                        upload.isPending ||
                        save.isPending ||
                        !uploadStatusesLoaded
                      }
                      onClick={() => {
                        if (selectedFile)
                          upload.mutate({
                            type: requirement.type,
                            file: selectedFile,
                          });
                      }}
                    >
                      {upload.isPending ? "Uploading..." : "Upload and scan"}
                    </Button>
                  </div>
                ) : null}
                {artifactUploads.length ? (
                  <ul className="internship-upload-statuses">
                    {artifactUploads.map((item) => (
                      <li key={item.upload_id}>
                        <StatusBadge tone={uploadTone(item.state)}>
                          {item.state}
                        </StatusBadge>
                        <span>{uploadStatusMessage(item)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="internship-muted">
                    No file has been uploaded for this artifact.
                  </p>
                )}
              </fieldset>
            );
          })}
        </div>
        {!immutable ? (
          <div className="internship-actions">
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || upload.isPending}
              variant="secondary"
            >
              {save.isPending ? "Saving..." : "Save draft"}
            </Button>
            <Button
              onClick={() => finalize.mutate()}
              disabled={
                finalize.isPending ||
                save.isPending ||
                upload.isPending ||
                !uploadStatusesLoaded ||
                !requiredArtifactsReady ||
                !allAttachedUploadsClean
              }
            >
              {finalize.isPending ? "Finalizing..." : "Finalize submission"}
            </Button>
          </div>
        ) : (
          <p className="internship-muted">
            Finalized versions are immutable and remain available for review.
          </p>
        )}
        {!immutable && uploadStatusesLoaded && !requiredArtifactsReady ? (
          <p className="internship-muted">
            Complete every required link and text field, and wait for every
            required file to be CLEAN before finalizing.
          </p>
        ) : null}
        {uploadError ? (
          <p className="form-error" role="alert">
            {uploadError}
          </p>
        ) : null}
        {uploadQueries.some((query) => query.isError) ? (
          <p className="form-error" role="alert">
            One or more upload statuses could not be refreshed. Retry before
            finalizing.
          </p>
        ) : null}
        {save.isError || finalize.isError ? (
          <p className="form-error" role="alert">
            The server rejected this change. Refresh the page to reconcile the
            latest version.
          </p>
        ) : null}
      </Card>

      <div className="multimodal-qa-container">
        <div className="multimodal-qa-banner">
          <div className="multimodal-qa-banner-content">
            <h3>Gemini Multimodal Deliverable & Artifact Review</h3>
            <p>
              Run automated computer vision and rubric inspection across your
              attached screenshots, diagrams, and project artifacts with Google
              Gemini 2.5 Flash.
            </p>
          </div>
          <Button
            onClick={() => runAiReview.mutate()}
            disabled={runAiReview.isPending}
            variant="primary"
          >
            {runAiReview.isPending
              ? "Analyzing with Gemini..."
              : "Run Gemini Multimodal Review"}
          </Button>
        </div>

        {aiReviewError ? (
          <p className="form-error" role="alert">
            {aiReviewError}
          </p>
        ) : null}

        {aiReview ? (
          <div className="multimodal-qa-result-card">
            <div className="multimodal-qa-topbar">
              <div
                style={{ display: "flex", alignItems: "center", gap: "12px" }}
              >
                <StatusBadge
                  tone={
                    aiReview.recommendation === "PASS" ? "success" : "warning"
                  }
                >
                  {aiReview.recommendation}
                </StatusBadge>
                <span className="multimodal-qa-score-badge">
                  Visual Score: {aiReview.overall_visual_score}/100
                </span>
              </div>
              <div className="multimodal-qa-meta">
                <span>Model: {aiReview.model_identifier}</span>
                <span>·</span>
                <span>Latency: {aiReview.latency_ms}ms</span>
                {aiReview.is_demo ? (
                  <>
                    <span>·</span>
                    <StatusBadge tone="ai">Deterministic Fixture</StatusBadge>
                  </>
                ) : null}
              </div>
            </div>

            <div className="multimodal-qa-section">
              <h4>Evaluation Summary</h4>
              <p style={{ margin: 0, fontSize: "14px", lineHeight: "1.5" }}>
                {aiReview.summary}
              </p>
            </div>

            <div className="multimodal-qa-section">
              <h4>Acceptance Criteria & Visual Evidence Findings</h4>
              <div style={{ display: "grid", gap: "10px" }}>
                {aiReview.criterion_findings.map((finding) => (
                  <div
                    className="multimodal-criterion-card"
                    key={finding.criterion_ordinal}
                  >
                    <div className="multimodal-criterion-header">
                      <span>Criterion #{finding.criterion_ordinal}</span>
                      <StatusBadge
                        tone={finding.passed ? "success" : "warning"}
                      >
                        {finding.passed ? "Passed" : "Action Required"} (
                        {Math.round(finding.confidence_score * 100)}%
                        confidence)
                      </StatusBadge>
                    </div>
                    <div className="multimodal-criterion-evidence">
                      {finding.visual_evidence_summary}
                    </div>
                    {finding.observed_features.length > 0 ? (
                      <div
                        style={{
                          display: "flex",
                          gap: "6px",
                          flexWrap: "wrap",
                          marginTop: "4px",
                        }}
                      >
                        {finding.observed_features.map((feature, i) => (
                          <span
                            key={i}
                            style={{
                              fontSize: "11px",
                              background: "rgba(7, 20, 31, 0.06)",
                              padding: "2px 8px",
                              borderRadius: "4px",
                            }}
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            {aiReview.identified_defects.length > 0 ? (
              <div className="multimodal-qa-section">
                <h4>Identified Visual Defects</h4>
                <div className="multimodal-defects-grid">
                  {aiReview.identified_defects.map((defect, i) => (
                    <div
                      key={i}
                      className={`multimodal-defect-item severity-${defect.severity}`}
                    >
                      <strong>
                        [{defect.category.toUpperCase()} -{" "}
                        {defect.severity.toUpperCase()}]
                      </strong>{" "}
                      {defect.description}
                      {defect.location_or_element ? (
                        <span
                          style={{ color: "var(--muted)", marginLeft: "6px" }}
                        >
                          (Element: {defect.location_or_element})
                        </span>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {aiReview.student_actionable_feedback.length > 0 ? (
              <div className="multimodal-qa-section">
                <h4>Actionable Student Feedback</h4>
                <div className="multimodal-feedback-box">
                  <ul>
                    {aiReview.student_actionable_feedback.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
