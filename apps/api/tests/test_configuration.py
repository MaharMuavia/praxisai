import pytest
from pydantic import ValidationError
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.db import engine_options


def test_production_refuses_demo_security_settings() -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(app_env="production", demo_mode=True, identity_provider="local")


def test_production_accepts_only_explicit_secure_provider_configuration() -> None:
    settings = Settings(
        app_env="production",
        demo_mode=False,
        identity_provider="firebase",
        firebase_project_id="praxis-production",
        gemini_provider="gemini",
        google_cloud_project="praxis-production",
        cloud_storage_bucket="praxis-production-artifacts",
        email_provider="smtp",
        email_from_address="operations@praxis.example",
        otel_exporter_otlp_endpoint="https://otel.praxis.example/v1/traces",
        api_base_url="https://api.praxis.example/api/v1",
        web_base_url="https://app.praxis.example",
        payment_provider="manual_external",
        credential_signing_provider="kms",
        credential_kms_key_name=(
            "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
            "cryptoKeyVersions/1"
        ),
        cookie_secure=True,
        session_secret="s" * 48,
        csrf_secret="c" * 48,
        cors_origins=["https://app.praxis.example"],
        database_url=("postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"),
        database_migration_url=(
            "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:5432/postgres"
        ),
        database_pool_mode="transaction",
    )

    assert settings.app_env == "production"


def test_transaction_pooling_disables_connection_and_statement_caches() -> None:
    settings = Settings(
        database_url=("postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"),
        database_migration_url=(
            "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:5432/postgres"
        ),
        database_pool_mode="transaction",
    )

    options = engine_options(settings)

    assert options["poolclass"] is NullPool
    assert options["connect_args"] == {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }


def test_generic_postgresql_urls_use_asyncpg_driver() -> None:
    settings = Settings(
        database_url="postgresql://postgres.ref:secret@pooler.example.test:6543/postgres",
        database_migration_url=("postgres://postgres.ref:secret@pooler.example.test:5432/postgres"),
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.database_migration_url == (
        "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:5432/postgres"
    )


def test_production_transaction_pool_requires_separate_migration_url() -> None:
    with pytest.raises(ValidationError, match="missing migration database URL"):
        Settings(
            _env_file=None,
            app_env="production",
            demo_mode=False,
            identity_provider="firebase",
            firebase_project_id="praxis-production",
        gemini_provider="gemini",
        google_cloud_project="praxis-production",
        cloud_storage_bucket="praxis-production-artifacts",
        email_provider="smtp",
        email_from_address="operations@praxis.example",
        otel_exporter_otlp_endpoint="https://otel.praxis.example/v1/traces",
        api_base_url="https://api.praxis.example/api/v1",
        web_base_url="https://app.praxis.example",
            credential_signing_provider="kms",
            credential_kms_key_name=(
                "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
                "cryptoKeyVersions/1"
            ),
            cookie_secure=True,
            session_secret="s" * 48,
            csrf_secret="c" * 48,
            cors_origins=["https://app.praxis.example"],
            database_url=(
                "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"
            ),
            database_pool_mode="transaction",
        )
