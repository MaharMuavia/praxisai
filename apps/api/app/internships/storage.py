import hashlib
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import quote

import httpx

from app.config import Settings


class LocalInternshipStorage:
    """Private, path-traversal-safe storage for local and demo environments."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if self.root not in candidate.parents:
            raise ValueError("Storage key escapes the private upload root")
        return candidate

    def put(self, storage_key: str, content: bytes) -> str:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def read(self, storage_key: str) -> bytes:
        return self._path(storage_key).read_bytes()

    async def put_stream(
        self, storage_key: str, chunks: AsyncIterator[bytes]
    ) -> tuple[str, int]:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with target.open("wb") as stream:
            async for chunk in chunks:
                digest.update(chunk)
                size += len(chunk)
                stream.write(chunk)
        return digest.hexdigest(), size


class SupabaseStorageError(RuntimeError):
    """A bounded, non-sensitive Supabase Storage provider failure."""


class SupabaseInternshipStorage:
    """Private Supabase Storage adapter using the server-only service-role key."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise SupabaseStorageError("Supabase Storage is not configured")
        if not settings.supabase_storage_bucket:
            raise SupabaseStorageError("Supabase Storage bucket is not configured")
        self._base_url = settings.supabase_url.rstrip("/")
        self._bucket = settings.supabase_storage_bucket
        self._service_role_key = settings.supabase_service_role_key
        self._timeout = settings.supabase_storage_timeout_seconds
        self._client = client

    def _object_url(self, storage_key: str) -> str:
        parts = storage_key.split("/")
        if not storage_key or storage_key.startswith("/") or ".." in parts:
            raise SupabaseStorageError("Invalid private storage key")
        bucket = quote(self._bucket, safe="")
        key = quote(storage_key, safe="/")
        return f"{self._base_url}/storage/v1/object/{bucket}/{key}"

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._service_role_key}",
            "apikey": self._service_role_key,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | AsyncIterator[bytes] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        if self._client is not None:
            response = await self._client.request(
                method, url, content=content, headers=headers, timeout=self._timeout
            )
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, url, content=content, headers=headers)
        if response.is_error:
            raise SupabaseStorageError(
                f"Supabase Storage request failed with HTTP {response.status_code}"
            )
        return response

    async def put(self, storage_key: str, content: bytes, content_type: str) -> str:
        await self._request(
            "POST",
            self._object_url(storage_key),
            content=content,
            headers={**self._headers(content_type), "x-upsert": "false"},
        )
        return hashlib.sha256(content).hexdigest()

    async def put_stream(
        self, storage_key: str, chunks: AsyncIterator[bytes], content_type: str, size: int
    ) -> tuple[str, int]:
        digest = hashlib.sha256()
        count = 0

        async def counted() -> AsyncIterator[bytes]:
            nonlocal count
            async for chunk in chunks:
                digest.update(chunk)
                count += len(chunk)
                yield chunk

        await self._request(
            "POST",
            self._object_url(storage_key),
            content=counted(),
            headers={
                **self._headers(content_type),
                "x-upsert": "false",
                "Content-Length": str(size),
            },
        )
        return digest.hexdigest(), count

    async def read(self, storage_key: str) -> bytes:
        response = await self._request(
            "GET", self._object_url(storage_key), headers=self._headers()
        )
        return response.content
