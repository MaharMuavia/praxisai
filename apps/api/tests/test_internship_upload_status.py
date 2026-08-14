import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionCodec, SessionPrincipal
from app.config import Settings, get_settings
from app.db import get_session
from app.domain.models import (
    Base,
    InternshipUpload,
    Organization,
    OrganizationMembership,
    User,
)
from app.main import app


@pytest.mark.asyncio
async def test_upload_status_is_visible_only_to_its_authenticated_owner() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    organization = Organization(name="Students", slug="upload-status-students", kind="program")
    owner = User(email="upload-owner@example.test", display_name="Upload owner")
    other_student = User(email="other-student@example.test", display_name="Other student")
    async with factory() as session:
        session.add_all([organization, owner, other_student])
        await session.flush()
        upload = InternshipUpload(
            upload_id="owner-upload-status",
            owner_user_id=owner.id,
            student_assignment_id=uuid.uuid4(),
            artifact_type="pdf",
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=4,
            sha256="0" * 64,
            storage_key="internships/owner/owner-upload-status/report.pdf",
            state="QUARANTINED",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scan_message="Awaiting malware scan",
        )
        session.add_all(
            [
                OrganizationMembership(
                    user_id=owner.id,
                    organization_id=organization.id,
                    role="student",
                ),
                OrganizationMembership(
                    user_id=other_student.id,
                    organization_id=organization.id,
                    role="student",
                ),
                upload,
            ]
        )
        await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    settings = Settings(_env_file=None)
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/internships/uploads/{upload.upload_id}")

        assert response.status_code == 401

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            owner_principal = SessionPrincipal(owner.id, organization.id, "student")
            client.cookies.set(
                "praxis_session",
                SessionCodec(settings.session_secret).encode(owner_principal),
            )
            response = await client.get(f"/api/v1/internships/uploads/{upload.upload_id}")

        assert response.status_code == 200
        payload = response.json()
        returned_expiry = datetime.fromisoformat(payload.pop("expires_at").replace("Z", "+00:00"))
        if returned_expiry.tzinfo is None:
            returned_expiry = returned_expiry.replace(tzinfo=UTC)
        assert returned_expiry == upload.expires_at
        assert payload == {
            "upload_id": upload.upload_id,
            "artifact_type": "pdf",
            "filename": "report.pdf",
            "state": "QUARANTINED",
            "upload_url": f"/api/v1/internships/uploads/{upload.upload_id}/content",
            "scan_message": "Awaiting malware scan",
        }

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            other_principal = SessionPrincipal(other_student.id, organization.id, "student")
            client.cookies.set(
                "praxis_session",
                SessionCodec(settings.session_secret).encode(other_principal),
            )
            response = await client.get(f"/api/v1/internships/uploads/{upload.upload_id}")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
