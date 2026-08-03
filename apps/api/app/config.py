from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path.cwd() / ".env", Path.cwd().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "test", "demo", "staging", "production"] = "local"
    demo_mode: bool = True
    api_base_url: str = "http://localhost:8000/api/v1"
    web_base_url: str = "http://localhost:3000"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://praxisai:praxisai_local@localhost:5432/praxisai"
    database_migration_url: str | None = None
    database_pool_mode: Literal["direct", "session", "transaction"] = "direct"
    session_secret: str = Field(default="local-session-secret-change-before-sharing", min_length=32)
    csrf_secret: str = Field(default="local-csrf-secret-change-before-sharing", min_length=32)
    cors_origins: list[str] = ["http://localhost:3000"]
    trusted_proxy_ips: list[str] = []
    cookie_secure: bool = False

    identity_provider: Literal["local", "firebase"] = "local"
    firebase_project_id: str | None = None
    firebase_credentials_json: str | None = None

    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    gemini_provider: Literal["disabled", "fixture", "gemini"] = "fixture"
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    cloud_storage_bucket: str | None = None

    payment_provider: Literal["manual_external"] = "manual_external"
    email_provider: Literal["disabled", "smtp", "sendgrid"] = "disabled"
    email_from_address: str | None = None
    otel_exporter_otlp_endpoint: str | None = None

    credential_signing_provider: Literal["demo", "kms"] = "demo"
    credential_kms_key_name: str | None = None
    credential_demo_private_key_path: Path = Path(".local/keys/credential-private.pem")
    credential_issuer: str = "PraxisAI Demo"
    university_minimum_cohort_size: int = Field(default=5, ge=5)

    @field_validator("database_url", "database_migration_url", mode="before")
    @classmethod
    def normalize_postgresql_driver(cls, value: str | None) -> str | None:
        """Use asyncpg when a provider gives the generic PostgreSQL URL scheme.

        Supabase displays libpq URLs beginning with ``postgresql://``. SQLAlchemy
        would otherwise select its synchronous psycopg2 dialect, which is not a
        dependency of this async application.
        """
        if value is None:
            return None
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgres://")
        return value

    @property
    def is_local_or_test(self) -> bool:
        return self.app_env in {"local", "test"}

    @property
    def is_demo_environment(self) -> bool:
        return self.app_env == "demo"

    @model_validator(mode="after")
    def reject_insecure_production(self) -> "Settings":
        if self.app_env not in {"staging", "production"}:
            if self.gemini_provider == "fixture" and not (self.demo_mode or self.app_env == "test"):
                raise ValueError("Fixture AI requires DEMO_MODE=true or APP_ENV=test")
            return self
        violations: list[str] = []
        if self.demo_mode:
            violations.append("DEMO_MODE")
        if self.identity_provider == "local":
            violations.append("local identity")
        if self.gemini_provider != "gemini":
            violations.append("GEMINI_PROVIDER=gemini")
        if self.credential_signing_provider == "demo":
            violations.append("demo credential signing")
        if not self.cookie_secure:
            violations.append("insecure cookies")
        if self.session_secret.startswith("local-") or self.csrf_secret.startswith("local-"):
            violations.append("default session or CSRF secrets")
        if "*" in self.cors_origins:
            violations.append("wildcard CORS")
        if self.identity_provider == "firebase" and not self.firebase_project_id:
            violations.append("missing Firebase project")
        if not self.google_cloud_project:
            violations.append("missing Vertex AI project")
        if self.credential_signing_provider == "kms" and not self.credential_kms_key_name:
            violations.append("missing KMS signing key")
        if not self.database_url.startswith("postgresql+asyncpg://"):
            violations.append("non-PostgreSQL production database")
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            violations.append("local production database")
        if self.database_pool_mode == "transaction" and not self.database_migration_url:
            violations.append("missing migration database URL for transaction pooling")
        if self.email_provider == "disabled" or not self.email_from_address:
            violations.append("missing transactional email configuration")
        if not self.otel_exporter_otlp_endpoint:
            violations.append("missing OpenTelemetry exporter")
        if not self.cloud_storage_bucket:
            violations.append("missing private artifact storage bucket")
        if any("localhost" in value or "127.0.0.1" in value for value in self.cors_origins):
            violations.append("local CORS origin")
        if "localhost" in self.api_base_url or "127.0.0.1" in self.api_base_url:
            violations.append("local API base URL")
        if "localhost" in self.web_base_url or "127.0.0.1" in self.web_base_url:
            violations.append("local web base URL")
        if violations:
            raise ValueError("Unsafe production configuration: " + ", ".join(violations))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
