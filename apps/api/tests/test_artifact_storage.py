import hashlib
import uuid
from unittest.mock import MagicMock

import pytest

from app.auth.service import SessionPrincipal
from app.config import Settings
from app.operations.artifacts import (
    ArtifactStorageService,
    ArtifactUploadRequest,
    SupabaseArtifactStorage,
    verify_content_hash,
)


def test_artifact_storage_cross_tenant_denial():
    settings = Settings(cloud_storage_bucket="praxisai-artifacts-bucket", app_env="test")
    service = ArtifactStorageService(settings, client=MagicMock())

    principal = SessionPrincipal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        role="student",
    )
    request = ArtifactUploadRequest(
        project_id=uuid.uuid4(),
        content_type="application/pdf",
        file_size_bytes=1024,
        content_hash="a" * 64,
    )

    allowed_projects = {uuid.uuid4()}  # Different project ID

    with pytest.raises(PermissionError, match="Cross-tenant artifact access denied"):
        service.generate_upload_url(principal, request, allowed_projects)


def test_artifact_storage_invalid_content_type():
    settings = Settings(cloud_storage_bucket="praxisai-artifacts-bucket", app_env="test")
    service = ArtifactStorageService(settings, client=MagicMock())

    project_id = uuid.uuid4()
    principal = SessionPrincipal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        role="student",
    )
    request = ArtifactUploadRequest(
        project_id=project_id,
        content_type="application/x-executable",
        file_size_bytes=1024,
        content_hash="b" * 64,
    )

    allowed_projects = {project_id}

    with pytest.raises(ValueError, match="Unsupported content type"):
        service.generate_upload_url(principal, request, allowed_projects)


def test_artifact_storage_quarantined_download_denied():
    settings = Settings(cloud_storage_bucket="praxisai-artifacts-bucket", app_env="test")
    service = ArtifactStorageService(settings, client=MagicMock())

    project_id = uuid.uuid4()
    principal = SessionPrincipal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        role="student",
    )
    object_name = f"artifacts/{project_id}/sample_uuid/{'c' * 64}"
    allowed_projects = {project_id}

    with pytest.raises(ValueError, match="quarantined"):
        service.generate_download_url(
            principal,
            project_id=project_id,
            object_name=object_name,
            scan_status="QUARANTINED",
            allowed_project_ids=allowed_projects,
        )


def test_content_hash_verification():
    data = b"PraxisAI immutable artifact content"
    expected = hashlib.sha256(data).hexdigest()
    assert verify_content_hash(data, expected) is True
    assert verify_content_hash(b"tampered content", expected) is False


def test_supabase_artifact_storage_uses_private_signed_urls():
    response = MagicMock(is_error=False)
    response.json.return_value = {"url": "/object/upload/sign/bucket/object"}
    client = MagicMock()
    client.request.return_value = response
    settings = Settings(
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="artifacts",
        app_env="test",
    )
    storage = SupabaseArtifactStorage(settings, client=client)

    assert storage.generate_upload_url("artifacts/demo/file.pdf", "application/pdf") == (
        "https://example.supabase.co/storage/v1/object/upload/sign/bucket/object"
    )
    client.request.assert_called_once()
    assert client.request.call_args.kwargs["headers"]["apikey"] == "service-role-secret"
