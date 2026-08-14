from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import NullPool

from app.config import Settings, migration_database_url
from app.db import engine_options

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_production_refuses_demo_security_settings() -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(app_env="production", demo_mode=True, identity_provider="local")


def test_production_accepts_only_explicit_secure_provider_configuration() -> None:
    settings = Settings(
        app_env="production",
        demo_mode=False,
        identity_provider="supabase",
        gemini_provider="gemini",
        google_cloud_project="praxis-production",
        cloud_storage_bucket="praxis-production-artifacts",
        storage_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_publishable_key="publishable-key",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="internship-submissions",
        web_base_url="https://app.praxis.example",
        payment_provider="manual_external",
        credential_signing_provider="kms",
        credential_kms_key_name=(
            "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
            "cryptoKeyVersions/1"
        ),
        cookie_secure=True,
        session_secret="s" * 48,
        cors_origins=["https://app.praxis.example"],
        database_url=("postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"),
        database_migration_url=(
            "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:5432/postgres"
        ),
        database_pool_mode="transaction",
        upload_scanner_provider="clamav",
        clamav_host="10.10.0.10",
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


def test_transaction_pool_requires_separate_url_only_for_migration_process() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        demo_mode=False,
        identity_provider="supabase",
        gemini_provider="gemini",
        google_cloud_project="praxis-production",
        cloud_storage_bucket="praxis-production-artifacts",
        storage_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_publishable_key="publishable-key",
        supabase_service_role_key="service-role-secret",
        supabase_storage_bucket="internship-submissions",
        web_base_url="https://app.praxis.example",
        credential_signing_provider="kms",
        credential_kms_key_name=(
            "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
            "cryptoKeyVersions/1"
        ),
        cookie_secure=True,
        session_secret="s" * 48,
        cors_origins=["https://app.praxis.example"],
        database_url=("postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"),
        database_pool_mode="transaction",
        upload_scanner_provider="clamav",
        clamav_host="10.10.0.10",
    )

    with pytest.raises(ValueError, match="DATABASE_MIGRATION_URL is required"):
        migration_database_url(settings)


def test_hosted_configuration_rejects_plaintext_provider_urls() -> None:
    with pytest.raises(ValidationError, match="non-HTTPS or malformed Supabase URL"):
        Settings(
            _env_file=None,
            app_env="production",
            demo_mode=False,
            identity_provider="supabase",
            gemini_provider="gemini",
            google_cloud_project="praxis-production",
            storage_provider="supabase",
            supabase_url="http://praxis.supabase.co",
            supabase_publishable_key="publishable-key",
            supabase_service_role_key="service-role-secret",
            web_base_url="https://app.praxis.example",
            credential_signing_provider="kms",
            credential_kms_key_name=(
                "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
                "cryptoKeyVersions/1"
            ),
            cookie_secure=True,
            session_secret="s" * 48,
            cors_origins=["https://app.praxis.example"],
            database_url=(
                "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"
            ),
            database_pool_mode="transaction",
            upload_scanner_provider="clamav",
            clamav_host="10.10.0.10",
        )


def test_production_worker_requires_only_its_runtime_dependencies() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        app_process_role="worker",
        demo_mode=False,
        storage_provider="supabase",
        supabase_url="https://praxis.supabase.co",
        supabase_service_role_key="service-role-secret",
        database_url=("postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"),
        database_pool_mode="transaction",
        upload_scanner_provider="clamav",
        clamav_host="10.10.0.10",
    )

    assert settings.app_process_role == "worker"


def test_production_worker_rejects_public_clamav_address() -> None:
    with pytest.raises(ValidationError, match="RFC1918 IPv4"):
        Settings(
            _env_file=None,
            app_env="production",
            app_process_role="worker",
            demo_mode=False,
            storage_provider="supabase",
            supabase_url="https://praxis.supabase.co",
            supabase_service_role_key="service-role-secret",
            database_url=(
                "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"
            ),
            database_pool_mode="transaction",
            upload_scanner_provider="clamav",
            clamav_host="203.0.113.10",
        )


def test_production_requires_a_kms_crypto_key_version_name() -> None:
    with pytest.raises(ValidationError, match="invalid KMS signing key version"):
        Settings(
            _env_file=None,
            app_env="production",
            demo_mode=False,
            identity_provider="supabase",
            gemini_provider="gemini",
            google_cloud_project="praxis-production",
            storage_provider="supabase",
            supabase_url="https://praxis.supabase.co",
            supabase_publishable_key="publishable-key",
            supabase_service_role_key="service-role-secret",
            web_base_url="https://app.praxis.example",
            credential_signing_provider="kms",
            credential_kms_key_name=(
                "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer"
            ),
            cookie_secure=True,
            session_secret="s" * 48,
            cors_origins=["https://app.praxis.example"],
            database_url=(
                "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:6543/postgres"
            ),
            database_migration_url=(
                "postgresql+asyncpg://postgres.ref:secret@pooler.example.test:5432/postgres"
            ),
            database_pool_mode="transaction",
            upload_scanner_provider="clamav",
            clamav_host="10.10.0.10",
        )


def test_deployment_contract_uses_supabase_auth_end_to_end() -> None:
    terraform = (REPOSITORY_ROOT / "infra" / "terraform" / "main.tf").read_text(encoding="utf-8")
    variables = (REPOSITORY_ROOT / "infra" / "terraform" / "variables.tf").read_text(
        encoding="utf-8"
    )
    release_workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "release-images.yml").read_text(
        encoding="utf-8"
    )

    assert 'IDENTITY_PROVIDER           = "supabase"' in terraform
    assert "SUPABASE_PUBLISHABLE_KEY" in terraform
    assert 'variable "supabase_publishable_key"' in variables
    assert "NEXT_PUBLIC_SUPABASE_URL" in release_workflow
    assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" in release_workflow
    assert 'resource "google_kms_crypto_key_version" "credentials"' in terraform
    assert (
        "CREDENTIAL_KMS_KEY_NAME     = var.credential_kms_enabled ? "
        "google_kms_crypto_key_version.credentials[0].name"
    ) in terraform
    assert "firebase" not in terraform.casefold()
    assert "firebase" not in variables.casefold()
    assert "firebase" not in release_workflow.casefold()


def test_deployment_contract_rejects_unsafe_release_inputs() -> None:
    terraform = (REPOSITORY_ROOT / "infra" / "terraform" / "main.tf").read_text(encoding="utf-8")
    variables = (REPOSITORY_ROOT / "infra" / "terraform" / "variables.tf").read_text(
        encoding="utf-8"
    )
    versions = (REPOSITORY_ROOT / "infra" / "terraform" / "versions.tf").read_text(encoding="utf-8")
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert 'backend "gcs" {}' in versions
    assert variables.count("@sha256:[0-9a-f]{64}$") == 2
    assert '"cloudkms.googleapis.com"' in terraform
    assert "bigquery.googleapis.com" not in terraform
    assert 'path = "/ready"' in terraform
    assert "*.tfstate" in gitignore
    assert "*.tfvars" in gitignore
    assert 'resource "google_cloud_run_v2_job" "worker"' in terraform
    assert 'command = ["python"]' in terraform
    assert 'args    = ["-m", "app.worker", "--limit", "10"]' in terraform
    assert 'resource "google_cloud_scheduler_job" "worker"' in terraform
    assert 'egress = "PRIVATE_RANGES_ONLY"' in terraform
    assert "worker_vpc_subnetwork" in terraform
    assert 'APP_PROCESS_ROLE            = "worker"' in terraform
    assert "google_secret_manager_secret_iam_member.api_database_migration" not in terraform
    assert 'name = "DATABASE_MIGRATION_URL"' not in terraform
    assert "google_monitoring_notification_channel.operator_email.name" in terraform
    assert 'version = "latest"' not in terraform
    assert terraform.count("lifecycle { prevent_destroy = true }") >= 8
