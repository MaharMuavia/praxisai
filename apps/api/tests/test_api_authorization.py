import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionCodec, SessionPrincipal
from app.config import get_settings
from app.db import get_session
from app.domain.models import Base, Organization, OrganizationMembership, Project, User
from app.main import app


def test_session_codec_accepts_a_pinned_rotation_fallback() -> None:
    principal = SessionPrincipal(uuid.uuid4(), uuid.uuid4(), "student")
    old_secret = "o" * 48
    new_secret = "n" * 48
    old_token = SessionCodec(old_secret).encode(principal)

    assert SessionCodec(new_secret, old_secret).decode(old_token) == principal
    with pytest.raises(ValueError, match="Invalid or expired session"):
        SessionCodec(new_secret).decode(old_token)


@pytest.mark.asyncio
async def test_client_cannot_read_another_organizations_project() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    first_org, second_org = (
        Organization(name="First", slug="first", kind="client"),
        Organization(name="Second", slug="second", kind="client"),
    )
    user = User(email="owner@example.test", display_name="Owner", is_demo=True)
    async with factory() as session:
        session.add_all([first_org, second_org, user])
        await session.flush()
        session.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=first_org.id,
                role="client_owner",
            )
        )
        other_project = Project(
            client_organization_id=second_org.id,
            created_by_id=user.id,
            title="Private second-tenant project",
            description="This project belongs to a different fictional client organization.",
            category="dashboard",
        )
        session.add(other_project)
        await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    principal = SessionPrincipal(user.id, first_org.id, "client_owner")
    token = SessionCodec(get_settings().session_secret).encode(principal)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set("praxis_session", token)
            response = await client.get(f"/api/v1/projects/{other_project.id}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "http_404"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
