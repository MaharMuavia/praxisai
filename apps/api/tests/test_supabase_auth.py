from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.auth.service import SupabaseIdentityProvider
from app.config import Settings


def provider() -> SupabaseIdentityProvider:
    return SupabaseIdentityProvider(
        Settings(
            identity_provider="supabase",
            supabase_url="https://praxisai.supabase.co",
            supabase_publishable_key="publishable-key",
            app_env="test",
        )
    )


def client(response: httpx.Response) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = mock_client
    return context


@pytest.mark.asyncio
async def test_supabase_identity_provider_valid() -> None:
    response = httpx.Response(
        200,
        json={
            "id": "user_123",
            "email": "user@example.com",
            "email_confirmed_at": "2026-08-08T00:00:00Z",
        },
    )
    with patch("httpx.AsyncClient", return_value=client(response)):
        identity = await provider().verify("valid_supabase_access_token")
    assert identity.subject == "user_123"
    assert identity.email == "user@example.com"


@pytest.mark.asyncio
async def test_supabase_identity_provider_rejects_unverified_email() -> None:
    response = httpx.Response(
        200,
        json={"id": "user_123", "email": "user@example.com"},
    )
    with patch("httpx.AsyncClient", return_value=client(response)):
        with pytest.raises(ValueError, match="email is not verified"):
            await provider().verify("unverified_supabase_access_token")


@pytest.mark.asyncio
async def test_supabase_identity_provider_rejects_auth_failure() -> None:
    response = httpx.Response(401, json={"msg": "invalid token"})
    with patch("httpx.AsyncClient", return_value=client(response)):
        with pytest.raises(ValueError, match="Invalid or expired"):
            await provider().verify("expired_supabase_access_token")


@pytest.mark.asyncio
async def test_supabase_identity_provider_handles_malformed_response() -> None:
    response = httpx.Response(200, content=b"not-json")
    with patch("httpx.AsyncClient", return_value=client(response)):
        with pytest.raises(ValueError, match="malformed identity"):
            await provider().verify("malformed_supabase_access_token")
