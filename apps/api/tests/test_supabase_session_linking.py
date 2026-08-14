from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.service import Identity
from app.config import Settings, get_settings
from app.db import get_session
from app.domain.models import Base, Organization, OrganizationMembership, User
from app.main import app


async def session_database(
    users: list[User], *, membership_user: User
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Students", slug="students", kind="student_program")
        session.add_all([organization, *users])
        await session.flush()
        session.add(
            OrganizationMembership(
                user_id=membership_user.id,
                organization_id=organization.id,
                role="student",
            )
        )
        await session.commit()
    return engine, factory


async def exchange_session(
    factory: async_sessionmaker[AsyncSession], identity: Identity
) -> Response:
    settings = Settings(
        _env_file=None,
        app_env="test",
        identity_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_publishable_key="publishable-key",
    )

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch(
            "app.api.auth.SupabaseIdentityProvider.verify",
            new=AsyncMock(return_value=identity),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.post(
                    "/api/v1/auth/session",
                    json={"access_token": "verified_supabase_access_token"},
                )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supabase_session_links_an_unbound_email_once() -> None:
    user = User(email="Student@Example.com", display_name="Student")
    engine, factory = await session_database([user], membership_user=user)
    try:
        response = await exchange_session(
            factory,
            Identity(subject="supabase-student", email="student@example.com"),
        )

        assert response.status_code == 204
        assert response.cookies.get("praxis_session")
        async with factory() as session:
            linked = await session.get(User, user.id)
            assert linked is not None
            assert linked.external_subject == "supabase-student"
            assert linked.email == "student@example.com"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_supabase_session_uses_bound_subject_and_updates_uncontested_email() -> None:
    user = User(
        email="old-address@example.com",
        display_name="Student",
        external_subject="supabase-student",
    )
    engine, factory = await session_database([user], membership_user=user)
    try:
        response = await exchange_session(
            factory,
            Identity(subject="supabase-student", email="new-address@example.com"),
        )

        assert response.status_code == 204
        async with factory() as session:
            linked = await session.get(User, user.id)
            assert linked is not None
            assert linked.email == "new-address@example.com"
            assert linked.external_subject == "supabase-student"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_supabase_session_rejects_split_subject_and_email_accounts() -> None:
    subject_user = User(
        email="subject-owner@example.com",
        display_name="Subject owner",
        external_subject="supabase-student",
    )
    email_user = User(
        email="verified-email@example.com",
        display_name="Email owner",
        external_subject="different-supabase-user",
    )
    engine, factory = await session_database(
        [subject_user, email_user], membership_user=subject_user
    )
    try:
        response = await exchange_session(
            factory,
            Identity(subject="supabase-student", email="verified-email@example.com"),
        )

        assert response.status_code == 409
        assert response.cookies.get("praxis_session") is None
        async with factory() as session:
            unchanged_subject = await session.get(User, subject_user.id)
            unchanged_email = await session.get(User, email_user.id)
            assert unchanged_subject is not None
            assert unchanged_email is not None
            assert unchanged_subject.email == "subject-owner@example.com"
            assert unchanged_subject.external_subject == "supabase-student"
            assert unchanged_email.external_subject == "different-supabase-user"
    finally:
        await engine.dispose()
