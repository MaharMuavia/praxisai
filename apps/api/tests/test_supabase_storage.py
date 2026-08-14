import httpx
import pytest

from app.config import Settings
from app.internships.storage import SupabaseInternshipStorage, SupabaseStorageError


@pytest.mark.asyncio
async def test_supabase_storage_uploads_and_reads_private_objects() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(200, json={"Key": "internships/student/upload/report.pdf"})
        return httpx.Response(200, content=b"report contents")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="internship-submissions",
    )
    storage = SupabaseInternshipStorage(settings, client=client)

    assert (
        await storage.put(
            "internships/student/upload/report.pdf", b"report contents", "application/pdf"
        )
        == "eb117536ada1f77ddf5d05a47c209a947be40675db476ef98e716d4d62aeb062"
    )
    assert await storage.read("internships/student/upload/report.pdf") == b"report contents"
    await client.aclose()

    assert requests[0].url.path.endswith(
        "/storage/v1/object/internship-submissions/internships/student/upload/report.pdf"
    )
    assert requests[0].headers["Authorization"] == "Bearer service-role-secret"
    assert requests[0].headers["apikey"] == "service-role-secret"


def test_supabase_storage_rejects_path_traversal() -> None:
    settings = Settings(
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="internship-submissions",
    )
    storage = SupabaseInternshipStorage(settings)

    with pytest.raises(SupabaseStorageError, match="Invalid private storage key"):
        storage._object_url("internships/../private/report.pdf")


@pytest.mark.asyncio
async def test_supabase_storage_translates_transport_failures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="internship-submissions",
    )
    storage = SupabaseInternshipStorage(settings, client=client)

    with pytest.raises(
        SupabaseStorageError, match="Supabase Storage is temporarily unavailable"
    ) as failure:
        await storage.read("internships/student/upload/report.pdf")
    await client.aclose()

    assert isinstance(failure.value.__cause__, httpx.ConnectError)


@pytest.mark.asyncio
async def test_supabase_storage_delete_is_idempotent_when_object_is_absent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(404, json={"message": "not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-secret",
    )

    await SupabaseInternshipStorage(settings, client=client).delete(
        "internships/student/missing.pdf"
    )
    await client.aclose()
