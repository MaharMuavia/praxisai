import time
from unittest.mock import patch

import pytest

from app.auth.service import FirebaseIdentityProvider
from app.config import Settings


@pytest.mark.asyncio
async def test_firebase_identity_provider_valid():
    settings = Settings(
        identity_provider="firebase",
        firebase_project_id="praxisai-test-project",
        app_env="test",
    )
    provider = FirebaseIdentityProvider(settings)

    mock_decoded = {
        "uid": "user_123",
        "email": "user@example.com",
        "email_verified": True,
        "aud": "praxisai-test-project",
        "iss": "https://securetoken.google.com/praxisai-test-project",
        "exp": int(time.time()) + 3600,
    }

    with patch("firebase_admin.auth.verify_id_token", return_value=mock_decoded):
        identity = await provider.verify("valid_token")
        assert identity.subject == "user_123"
        assert identity.email == "user@example.com"


@pytest.mark.asyncio
async def test_firebase_identity_provider_unverified_email():
    settings = Settings(
        identity_provider="firebase",
        firebase_project_id="praxisai-test-project",
        app_env="test",
    )
    provider = FirebaseIdentityProvider(settings)

    mock_decoded = {
        "uid": "user_123",
        "email": "user@example.com",
        "email_verified": False,
        "aud": "praxisai-test-project",
        "iss": "https://securetoken.google.com/praxisai-test-project",
        "exp": int(time.time()) + 3600,
    }

    with patch("firebase_admin.auth.verify_id_token", return_value=mock_decoded):
        with pytest.raises(ValueError, match="no verified email"):
            await provider.verify("unverified_token")


@pytest.mark.asyncio
async def test_firebase_identity_provider_cross_project():
    settings = Settings(
        identity_provider="firebase",
        firebase_project_id="praxisai-test-project",
        app_env="test",
    )
    provider = FirebaseIdentityProvider(settings)

    mock_decoded = {
        "uid": "user_123",
        "email": "user@example.com",
        "email_verified": True,
        "aud": "other-project-id",
        "iss": "https://securetoken.google.com/other-project-id",
        "exp": int(time.time()) + 3600,
    }

    with patch("firebase_admin.auth.verify_id_token", return_value=mock_decoded):
        with pytest.raises(ValueError, match="Cross-project identity rejected"):
            await provider.verify("cross_project_token")


@pytest.mark.asyncio
async def test_firebase_identity_provider_expired():
    settings = Settings(
        identity_provider="firebase",
        firebase_project_id="praxisai-test-project",
        app_env="test",
    )
    provider = FirebaseIdentityProvider(settings)

    mock_decoded = {
        "uid": "user_123",
        "email": "user@example.com",
        "email_verified": True,
        "aud": "praxisai-test-project",
        "iss": "https://securetoken.google.com/praxisai-test-project",
        "exp": int(time.time()) - 10,
    }

    with patch("firebase_admin.auth.verify_id_token", return_value=mock_decoded):
        with pytest.raises(ValueError, match="expired"):
            await provider.verify("expired_token")
