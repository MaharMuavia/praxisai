import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SubmissionDraft } from "@/lib/queries/internships/submissions";
import { InternshipSubmissionEditor } from "./internship-submission-editor";

const submission: SubmissionDraft = {
  id: "submission-1",
  student_assignment_id: "assignment-1",
  version: 1,
  state: "DRAFT",
  links: {},
  text_fields: {},
  artifact_upload_ids: [],
  canonical_hash: null,
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function assignment(
  requiredArtifactTypes: { type: string; required: boolean }[],
) {
  return {
    id: "assignment-1",
    title: "Production evidence",
    summary: "",
    problem_statement: "",
    objectives: [],
    deliverables: [],
    acceptance_criteria: [],
    required_artifact_types: requiredArtifactTypes,
    state: "IN_PROGRESS",
    release_at: "2026-08-01T00:00:00Z",
    due_at: "2026-08-30T00:00:00Z",
    submitted_at: null,
    attempt_count: 1,
    current_submission_id: "submission-1",
    is_late: false,
  };
}

function renderEditor() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <InternshipSubmissionEditor submissionId="submission-1" />
    </QueryClientProvider>,
  );
}

describe("InternshipSubmissionEditor", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders and saves a required dynamic text artifact", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockImplementation(async (input, init) => {
        const url = String(input);
        if (
          url.endsWith("/internships/me/submissions/submission-1") &&
          !init?.method
        ) {
          return jsonResponse(submission);
        }
        if (url.endsWith("/internships/me/assignments/assignment-1")) {
          return jsonResponse(
            assignment([{ type: "evaluation_plan", required: true }]),
          );
        }
        if (
          url.endsWith("/internships/me/submissions/submission-1") &&
          init?.method === "PUT"
        ) {
          const body = JSON.parse(String(init.body)) as {
            expected_version: number;
            text_fields: Record<string, string>;
          };
          return jsonResponse({
            ...submission,
            version: body.expected_version + 1,
            text_fields: body.text_fields,
          });
        }
        return new Response(null, { status: 404 });
      });
    renderEditor();

    const input = await screen.findByLabelText("Evaluation plan (required)");
    expect(
      screen.getByRole("button", { name: "Finalize submission" }),
    ).toBeDisabled();
    fireEvent.change(input, {
      target: { value: "Measure precision and recall weekly." },
    });
    expect(
      screen.getByRole("button", { name: "Finalize submission" }),
    ).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    await waitFor(() => {
      const update = fetchMock.mock.calls.find(
        ([request, requestInit]) =>
          String(request).endsWith(
            "/internships/me/submissions/submission-1",
          ) && requestInit?.method === "PUT",
      );
      expect(JSON.parse(String(update?.[1]?.body))).toMatchObject({
        expected_version: 1,
        text_fields: {
          evaluation_plan: "Measure precision and recall weekly.",
        },
      });
    });
  });

  it("uploads, persists, and polls a required file until it is CLEAN", async () => {
    let currentSubmission = { ...submission };
    let statusReads = 0;
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockImplementation(async (input, init) => {
        const url = String(input);
        if (
          url.endsWith("/internships/me/submissions/submission-1") &&
          !init?.method
        ) {
          return jsonResponse(currentSubmission);
        }
        if (url.endsWith("/internships/me/assignments/assignment-1")) {
          return jsonResponse(
            assignment([{ type: "screenshots", required: true }]),
          );
        }
        if (url.endsWith("/internships/uploads/initiate")) {
          return jsonResponse(
            {
              upload_id: "upload-1",
              artifact_type: "screenshots",
              filename: "evidence.png",
              state: "INITIATED",
              expires_at: "2026-08-30T00:00:00Z",
              upload_url: "/api/v1/internships/uploads/upload-1/content",
            },
            201,
          );
        }
        if (
          url.endsWith("/internships/uploads/upload-1/content") &&
          init?.method === "PUT"
        ) {
          expect(init.body).toBeInstanceOf(File);
          return jsonResponse({
            upload_id: "upload-1",
            artifact_type: "screenshots",
            filename: "evidence.png",
            state: "UPLOADED",
            expires_at: "2026-08-30T00:00:00Z",
            upload_url: "/api/v1/internships/uploads/upload-1/content",
          });
        }
        if (url.endsWith("/internships/uploads/upload-1/complete")) {
          return jsonResponse({
            upload_id: "upload-1",
            artifact_type: "screenshots",
            filename: "evidence.png",
            state: "QUARANTINED",
            expires_at: "2026-08-30T00:00:00Z",
            upload_url: "/api/v1/internships/uploads/upload-1/content",
          });
        }
        if (
          url.endsWith("/internships/me/submissions/submission-1") &&
          init?.method === "PUT"
        ) {
          const body = JSON.parse(String(init.body)) as {
            artifact_upload_ids: string[];
            expected_version: number;
          };
          currentSubmission = {
            ...currentSubmission,
            version: body.expected_version + 1,
            artifact_upload_ids: body.artifact_upload_ids,
          };
          return jsonResponse(currentSubmission);
        }
        if (url.endsWith("/internships/uploads/upload-1")) {
          statusReads += 1;
          return jsonResponse({
            upload_id: "upload-1",
            artifact_type: "screenshots",
            filename: "evidence.png",
            state: "CLEAN",
            expires_at: "2026-08-30T00:00:00Z",
            upload_url: "/api/v1/internships/uploads/upload-1/content",
          });
        }
        return new Response(null, { status: 404 });
      });
    vi.spyOn(crypto.subtle, "digest").mockResolvedValue(
      new Uint8Array(32).buffer,
    );
    renderEditor();

    const fileInput = await screen.findByLabelText("screenshots (required)");
    const file = new File([new Uint8Array([137, 80, 78, 71])], "evidence.png", {
      type: "image/png",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload and scan" }));

    expect(
      await screen.findByText(/quarantined while malware scanning/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Finalize submission" }),
    ).toBeDisabled();
    await waitFor(
      () =>
        expect(
          screen.getByText(/clean and ready to attach/),
        ).toBeInTheDocument(),
      { timeout: 4_000 },
    );
    expect(
      screen.getByRole("button", { name: "Finalize submission" }),
    ).toBeEnabled();
    expect(statusReads).toBeGreaterThan(0);

    const completes = fetchMock.mock.calls.filter(([request]) =>
      String(request).endsWith("/internships/uploads/upload-1/complete"),
    );
    expect(completes).toHaveLength(1);
    const persisted = fetchMock.mock.calls.find(
      ([request, requestInit]) =>
        String(request).endsWith("/internships/me/submissions/submission-1") &&
        requestInit?.method === "PUT",
    );
    expect(JSON.parse(String(persisted?.[1]?.body))).toMatchObject({
      artifact_upload_ids: ["upload-1"],
    });
  });
});
