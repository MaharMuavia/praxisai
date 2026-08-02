import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from google.cloud import storage  # type: ignore[attr-defined]
from pydantic import BaseModel, Field

from app.auth.service import SessionPrincipal
from app.config import Settings

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/json",
    "application/zip",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/markdown",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class ArtifactUploadRequest(BaseModel):
    project_id: uuid.UUID
    content_type: str
    file_size_bytes: int = Field(ge=1, le=MAX_FILE_SIZE_BYTES)
    content_hash: str = Field(min_length=64, max_length=64)


@dataclass(frozen=True)
class SignedUrlResponse:
    url: str
    object_name: str
    expires_at: datetime
    content_hash: str


class ArtifactStorageService:
    def __init__(self, settings: Settings, client: storage.Client | None = None) -> None:
        self._bucket_name = settings.cloud_storage_bucket
        self._client = client

    def _get_client(self) -> storage.Client:
        if self._client is not None:
            return self._client
        return storage.Client()

    def generate_upload_url(
        self,
        principal: SessionPrincipal,
        request: ArtifactUploadRequest,
        allowed_project_ids: set[uuid.UUID],
    ) -> SignedUrlResponse:
        # Authorization check: verify user belongs to the project's organization
        if request.project_id not in allowed_project_ids:
            raise PermissionError("Cross-tenant artifact access denied")

        # Content type restriction
        if request.content_type.lower() not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {request.content_type}")

        if not self._bucket_name:
            raise ValueError("Cloud Storage bucket is not configured")

        random_id = uuid.uuid4()
        object_name = f"artifacts/{request.project_id}/{random_id}/{request.content_hash}"
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(object_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=request.content_type,
        )

        return SignedUrlResponse(
            url=url,
            object_name=object_name,
            expires_at=expires_at,
            content_hash=request.content_hash,
        )

    def generate_download_url(
        self,
        principal: SessionPrincipal,
        project_id: uuid.UUID,
        object_name: str,
        scan_status: str,
        allowed_project_ids: set[uuid.UUID],
    ) -> SignedUrlResponse:
        if project_id not in allowed_project_ids:
            raise PermissionError("Cross-tenant artifact access denied")

        if not object_name.startswith(f"artifacts/{project_id}/"):
            raise PermissionError("Object does not belong to the requested project")

        if scan_status == "QUARANTINED":
            raise ValueError("File is quarantined by malware scanner")

        if not self._bucket_name:
            raise ValueError("Cloud Storage bucket is not configured")

        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(object_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="GET",
        )

        content_hash = object_name.split("/")[-1]
        return SignedUrlResponse(
            url=url,
            object_name=object_name,
            expires_at=expires_at,
            content_hash=content_hash,
        )


def verify_content_hash(data: bytes, expected_hash: str) -> bool:
    actual = hashlib.sha256(data).hexdigest()
    return actual.lower() == expected_hash.lower()
