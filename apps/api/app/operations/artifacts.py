import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import httpx
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


class SupabaseArtifactStorage:
    """Synchronous signed-URL adapter for the legacy commercial artifact boundary."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Supabase Storage is not configured")
        self._base_url = settings.supabase_url.rstrip("/")
        self._bucket = settings.supabase_storage_bucket
        self._key = settings.supabase_service_role_key
        self._timeout = settings.supabase_storage_timeout_seconds
        self._client = client

    def _endpoint(self, operation: str, object_name: str) -> str:
        if not object_name or object_name.startswith("/") or ".." in object_name.split("/"):
            raise ValueError("Invalid private storage key")
        bucket = quote(self._bucket, safe="")
        path = quote(object_name, safe="/")
        return f"{self._base_url}/storage/v1/object/{operation}/{bucket}/{path}"

    def _request(self, method: str, url: str, *, payload: dict[str, object]) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self._key}",
            "apikey": self._key,
        }
        if self._client is not None:
            response = self._client.request(method, url, headers=headers, json=payload)
        else:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(method, url, headers=headers, json=payload)
        if response.is_error:
            raise ValueError(f"Supabase Storage request failed with HTTP {response.status_code}")
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Supabase Storage returned an invalid signed URL response")
        return data

    def _absolute_url(self, value: object) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError("Supabase Storage did not return a signed URL")
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return f"{self._base_url}/storage/v1{value if value.startswith('/') else '/' + value}"

    def generate_upload_url(self, object_name: str, content_type: str) -> str:
        data = self._request(
            "POST",
            self._endpoint("upload/sign", object_name),
            payload={"upsert": False, "contentType": content_type},
        )
        return self._absolute_url(data.get("url") or data.get("signedURL") or data.get("signedUrl"))

    def generate_download_url(self, object_name: str, expires_in: int) -> str:
        data = self._request(
            "POST",
            self._endpoint("sign", object_name),
            payload={"expiresIn": expires_in},
        )
        return self._absolute_url(data.get("signedURL") or data.get("signedUrl") or data.get("url"))


class ArtifactStorageService:
    def __init__(
        self,
        settings: Settings,
        client: storage.Client | None = None,
        supabase_client: httpx.Client | None = None,
    ) -> None:
        self._use_supabase = settings.storage_provider == "supabase"
        self._bucket_name = settings.cloud_storage_bucket
        self._client = client
        self._supabase = (
            SupabaseArtifactStorage(settings, client=supabase_client)
            if self._use_supabase
            else None
        )

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

        random_id = uuid.uuid4()
        object_name = f"artifacts/{request.project_id}/{random_id}/{request.content_hash}"
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        if self._supabase is not None:
            url = self._supabase.generate_upload_url(object_name, request.content_type)
            return SignedUrlResponse(
                url=url,
                object_name=object_name,
                expires_at=expires_at,
                content_hash=request.content_hash,
            )

        if not self._bucket_name:
            raise ValueError("Cloud Storage bucket is not configured")

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

        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        if self._supabase is not None:
            url = self._supabase.generate_download_url(object_name, 15 * 60)
            return SignedUrlResponse(
                url=url,
                object_name=object_name,
                expires_at=expires_at,
                content_hash=object_name.split("/")[-1],
            )

        if not self._bucket_name:
            raise ValueError("Cloud Storage bucket is not configured")
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
