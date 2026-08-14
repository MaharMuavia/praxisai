import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import main
from app.readiness import EXPECTED_DATABASE_REVISIONS


@pytest.mark.asyncio
async def test_health_is_available_at_root_and_api_prefix() -> None:
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        root_response = await client.get("/health")
        api_response = await client.get("/api/v1/health")

    assert root_response.status_code == 200
    assert api_response.status_code == 200
    assert root_response.json() == {"status": "ok"}
    assert api_response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_validation_errors_do_not_echo_sensitive_input() -> None:
    sensitive_value = "short-secret-token"
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/session",
            json={"access_token": sensitive_value},
        )

    assert response.status_code == 422
    assert sensitive_value not in response.text
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]["errors"] == [
        {
            "type": "string_too_short",
            "loc": ["body", "access_token"],
            "msg": "String should have at least 20 characters",
        }
    ]


@pytest.mark.asyncio
async def test_readiness_requires_the_current_database_migration(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": next(iter(EXPECTED_DATABASE_REVISIONS))},
        )
    monkeypatch.setattr(main, "SessionFactory", factory)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            root_response = await client.get("/ready")
            api_response = await client.get("/api/v1/ready")
    finally:
        await engine.dispose()

    assert root_response.status_code == 200
    assert api_response.status_code == 200
    assert root_response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_readiness_rejects_a_stale_database_without_leaking_details(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('stale-revision')")
        )
    monkeypatch.setattr(main, "SessionFactory", factory)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.get("/ready")
    finally:
        await engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
