import { internshipFetch } from "./shared";

export type InternshipUpload = {
  upload_id: string;
  artifact_type: string;
  filename: string;
  state: string;
  expires_at: string;
  upload_url: string;
};

export const internshipUploadKey = (uploadId: string) =>
  ["internships", "upload", uploadId] as const;

const contentTypesByExtension: Readonly<Record<string, readonly string[]>> = {
  pdf: ["application/pdf"],
  png: ["image/png"],
  jpg: ["image/jpeg"],
  jpeg: ["image/jpeg"],
  webp: ["image/webp"],
  zip: ["application/zip", "application/x-zip-compressed"],
  ipynb: ["application/json"],
  json: ["application/json"],
  md: ["text/markdown", "text/plain"],
  txt: ["text/plain"],
};

function parseUpload(value: unknown): InternshipUpload {
  if (typeof value !== "object" || value === null) {
    throw new Error("The upload service returned an invalid response.");
  }
  const record = value as Record<string, unknown>;
  for (const key of [
    "upload_id",
    "artifact_type",
    "filename",
    "state",
    "expires_at",
    "upload_url",
  ] as const) {
    if (typeof record[key] !== "string" || record[key].length === 0) {
      throw new Error("The upload service returned an invalid response.");
    }
  }
  return {
    upload_id: record.upload_id as string,
    artifact_type: record.artifact_type as string,
    filename: record.filename as string,
    state: record.state as string,
    expires_at: record.expires_at as string,
    upload_url: record.upload_url as string,
  };
}

function fileContentType(file: File): string {
  const extension = file.name.split(".").at(-1)?.toLowerCase() ?? "";
  const allowed = contentTypesByExtension[extension];
  if (!allowed) {
    throw new Error(
      "This file type is not accepted. Use PDF, PNG, JPEG, WebP, ZIP, notebook, JSON, Markdown, or plain text.",
    );
  }
  const normalized = file.type.split(";", 1)[0].trim().toLowerCase();
  if (normalized && !allowed.includes(normalized)) {
    throw new Error(
      "The selected file extension and content type do not match.",
    );
  }
  return normalized || allowed[0];
}

function csrfHeader(): Record<string, string> {
  const token = document.cookie
    .split("; ")
    .find((value) => value.startsWith("praxis_csrf="))
    ?.split("=", 2)[1];
  return token ? { "X-CSRF-Token": decodeURIComponent(token) } : {};
}

function validatedUploadTarget(upload: InternshipUpload): string {
  const expectedPath = `/api/v1/internships/uploads/${encodeURIComponent(upload.upload_id)}/content`;
  const target = new URL(upload.upload_url, window.location.origin);
  if (
    target.origin !== window.location.origin ||
    target.pathname !== expectedPath ||
    target.search !== "" ||
    target.hash !== ""
  ) {
    throw new Error("The upload service returned an unsafe upload target.");
  }
  return expectedPath;
}

async function sha256Hex(file: File): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    await file.arrayBuffer(),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

async function putUploadContent(
  upload: InternshipUpload,
  file: File,
  contentType: string,
): Promise<void> {
  const response = await fetch(validatedUploadTarget(upload), {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": contentType, ...csrfHeader() },
    body: file,
  });
  if (!response.ok) {
    throw new Error(`The file transfer failed (${response.status}).`);
  }
  parseUpload(await response.json());
}

export async function uploadInternshipArtifact(
  assignmentId: string,
  artifactType: string,
  file: File,
): Promise<InternshipUpload> {
  if (file.size <= 0) throw new Error("The selected file is empty.");
  const contentType = fileContentType(file);
  const sha256 = await sha256Hex(file);
  const initiated = parseUpload(
    await internshipFetch<unknown>("/internships/uploads/initiate", {
      method: "POST",
      body: JSON.stringify({
        assignment_id: assignmentId,
        artifact_type: artifactType,
        filename: file.name,
        content_type: contentType,
        size_bytes: file.size,
        sha256,
      }),
    }),
  );
  if (initiated.artifact_type !== artifactType) {
    throw new Error("The upload service returned the wrong artifact type.");
  }
  await putUploadContent(initiated, file, contentType);
  return parseUpload(
    await internshipFetch<unknown>(
      `/internships/uploads/${encodeURIComponent(initiated.upload_id)}/complete`,
      { method: "POST", body: JSON.stringify({ sha256 }) },
    ),
  );
}

export async function getInternshipUpload(
  uploadId: string,
): Promise<InternshipUpload> {
  return parseUpload(
    await internshipFetch<unknown>(
      `/internships/uploads/${encodeURIComponent(uploadId)}`,
    ),
  );
}
