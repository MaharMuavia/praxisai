import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import auth as auth_routes
from app.api import credentials as credential_routes
from app.api import intake as intake_routes
from app.api.projects import _enforce_rate_limit
from app.auth.service import Identity, SessionPrincipal
from app.config import Settings, get_settings
from app.db import get_session
from app.domain.models import Base, OrganizationMembership, User
from app.domain.schemas import LocalSessionRequest, SupabaseSessionRequest
from app.main import app
from app.rate_limits.service import opaque_rate_limit_key


def test_opaque_rate_limit_key_is_stable_and_does_not_retain_the_identifier() -> None:
    first = opaque_rate_limit_key(
        namespace="public-intake:email",
        identifier="student@example.test",
    )
    repeated = opaque_rate_limit_key(
        namespace="public-intake:email",
        identifier="student@example.test",
    )
    different = opaque_rate_limit_key(
        namespace="public-intake:email",
        identifier="other@example.test",
    )

    assert first == repeated
    assert first != different
    assert "student@example.test" not in first


@pytest.mark.asyncio
async def test_authenticated_limit_uses_the_verified_user_and_does_not_commit() -> None:
    session = AsyncMock(spec=AsyncSession)
    principal = SessionPrincipal(uuid.uuid4(), uuid.uuid4(), "coordinator")
    consume = AsyncMock()

    with patch("app.api.projects.consume_rate_limit", consume):
        await _enforce_rate_limit(
            session,
            principal,
            category="agent:qa",
            limit=10,
            window_seconds=60,
        )

    consume.assert_awaited_once_with(
        session,
        raw_key=opaque_rate_limit_key(
            namespace="agent:qa:user",
            identifier=str(principal.user_id),
        ),
        limit=10,
        window_seconds=60,
        commit=False,
    )


@pytest.mark.asyncio
async def test_unauthenticated_project_request_cannot_consume_a_user_limit() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_session
    consume = AsyncMock()
    try:
        with patch("app.api.projects.consume_rate_limit", consume):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/projects/{uuid.uuid4()}/deliverables",
                    headers={
                        "Forwarded": "for=198.51.100.10",
                        "X-Forwarded-For": "198.51.100.11",
                        "X-Real-IP": "198.51.100.12",
                    },
                    json={
                        "title": "Attempted artifact",
                        "artifact_kind": "deployment",
                        "artifact_uri": "https://example.test/artifact",
                    },
                )

        assert response.status_code == 401
        consume.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_local_session_limits_the_validated_membership_user() -> None:
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    membership = OrganizationMembership(
        user_id=user_id,
        organization_id=organization_id,
        role="student",
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = membership
    enforce = AsyncMock()
    response = Response()

    with patch("app.api.auth._enforce_auth_rate_limit", enforce):
        await auth_routes.local_session(
            LocalSessionRequest(
                user_id=user_id,
                organization_id=organization_id,
                role="student",
            ),
            response,
            session,
            Settings(_env_file=None, app_env="test", demo_mode=True),
        )

    assert [item.kwargs for item in enforce.await_args_list] == [
        {
            "raw_key": "auth:local:global",
            "limit": auth_routes.AUTH_GLOBAL_RATE_LIMIT,
        },
        {
            "raw_key": opaque_rate_limit_key(
                namespace="auth:local:user",
                identifier=str(user_id),
            ),
            "limit": auth_routes.AUTH_LOCAL_USER_RATE_LIMIT,
        },
    ]


@pytest.mark.asyncio
async def test_supabase_preverification_limits_ignore_forwarding_headers() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    settings = Settings(
        _env_file=None,
        app_env="test",
        identity_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_publishable_key="publishable-key",
    )
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    token = "invalid_supabase_access_token_long_enough"
    consume = AsyncMock()
    verify = AsyncMock(side_effect=ValueError("Invalid or expired Supabase identity"))
    try:
        with (
            patch("app.api.auth.consume_rate_limit", consume),
            patch("app.api.auth.SupabaseIdentityProvider.verify", verify),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                responses = []
                for address in ("198.51.100.20", "203.0.113.30"):
                    responses.append(
                        await client.post(
                            "/api/v1/auth/session",
                            headers={
                                "Forwarded": f"for={address}",
                                "X-Forwarded-For": address,
                                "X-Real-IP": address,
                            },
                            json={"access_token": token},
                        )
                    )

        assert [response.status_code for response in responses] == [401, 401]
        expected_keys = [
            opaque_rate_limit_key(
                namespace="auth:supabase:token",
                identifier=token,
            ),
            "auth:supabase:global",
        ] * 2
        assert [item.kwargs["raw_key"] for item in consume.await_args_list] == expected_keys
        assert all(
            address not in str(consume.await_args_list)
            for address in ("198.51.100.20", "203.0.113.30")
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supabase_session_adds_a_verified_subject_limit() -> None:
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    identity = Identity(subject="supabase-user-123", email="student@example.test")
    user = User(
        id=user_id,
        email=identity.email,
        display_name="Student",
        external_subject=identity.subject,
        is_active=True,
    )
    membership = OrganizationMembership(
        user_id=user_id,
        organization_id=organization_id,
        role="student",
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = membership
    enforce = AsyncMock()
    token = "verified_supabase_access_token_long_enough"
    settings = Settings(
        _env_file=None,
        app_env="test",
        identity_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_publishable_key="publishable-key",
    )

    with (
        patch("app.api.auth._enforce_auth_rate_limit", enforce),
        patch(
            "app.api.auth.SupabaseIdentityProvider.verify",
            new=AsyncMock(return_value=identity),
        ),
        patch(
            "app.api.auth.resolve_or_link_identity_user",
            new=AsyncMock(return_value=user),
        ),
    ):
        await auth_routes.supabase_session(
            SupabaseSessionRequest(access_token=token),
            Response(),
            session,
            settings,
        )

    assert [item.kwargs for item in enforce.await_args_list] == [
        {
            "raw_key": opaque_rate_limit_key(
                namespace="auth:supabase:token",
                identifier=token,
            ),
            "limit": auth_routes.AUTH_SUPABASE_TOKEN_RATE_LIMIT,
        },
        {
            "raw_key": "auth:supabase:global",
            "limit": auth_routes.AUTH_GLOBAL_RATE_LIMIT,
        },
        {
            "raw_key": opaque_rate_limit_key(
                namespace="auth:supabase:subject",
                identifier=identity.subject,
            ),
            "limit": auth_routes.AUTH_SUPABASE_SUBJECT_RATE_LIMIT,
        },
    ]


@pytest.mark.asyncio
async def test_public_credential_limit_cannot_be_bypassed_with_forwarding_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    monkeypatch.setattr(credential_routes, "PUBLIC_CREDENTIAL_RESOURCE_LIMIT", 2)
    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            responses = []
            for address in ("198.51.100.40", "203.0.113.50", "192.0.2.60"):
                responses.append(
                    await client.get(
                        "/api/v1/public/credentials/nonexistent-public-slug",
                        headers={
                            "Forwarded": f"for={address}",
                            "X-Forwarded-For": address,
                            "X-Real-IP": address,
                        },
                    )
                )

        assert [response.status_code for response in responses] == [200, 200, 429]
        assert responses[0].json()["status"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_intake_limit_cannot_be_bypassed_with_forwarding_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    payload = {
        "kind": "company",
        "full_name": "Rate Limited Example",
        "email": "rate-limit@example.org",
        "country": "Pakistan",
        "consent": True,
        "company_name": "Example Studio",
        "business_problem": "We need a reviewed workflow for a recurring internal process.",
        "desired_result": "A tested and documented review surface for the operations team.",
        "project_category": "workflow_automation",
        "target_timeline": "This quarter",
        "data_sensitivity": "internal",
        "honeypot": "",
    }
    monkeypatch.setattr(intake_routes, "PUBLIC_INTAKE_EMAIL_LIMIT", 2)
    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            responses = []
            for index, address in enumerate(
                ("198.51.100.70", "203.0.113.80", "192.0.2.90"), start=1
            ):
                responses.append(
                    await client.post(
                        "/api/v1/public/company",
                        headers={
                            "Idempotency-Key": f"rate-limit-intake-{index}",
                            "Forwarded": f"for={address}",
                            "X-Forwarded-For": address,
                            "X-Real-IP": address,
                        },
                        json=payload,
                    )
                )

        assert [response.status_code for response in responses] == [201, 201, 429]
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
