import re
from functools import lru_cache
from ipaddress import IPv4Address, IPv4Network, ip_address
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.internships.limits import MAX_CONFIGURABLE_UPLOAD_BYTES


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path.cwd() / ".env", Path.cwd().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "test", "demo", "staging", "production"] = "local"
    app_process_role: Literal["api", "worker"] = "api"
    demo_mode: bool = True
    web_base_url: str = "http://localhost:3000"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://praxisai:praxisai_local@localhost:5432/praxisai"
    database_migration_url: str | None = None
    database_pool_mode: Literal["direct", "session", "transaction"] = "direct"
    storage_provider: Literal["local", "supabase", "gcs"] = "local"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "internship-submissions"
    supabase_storage_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    internship_max_upload_bytes: int = Field(
        default=30 * 1024 * 1024,
        ge=1024,
        le=MAX_CONFIGURABLE_UPLOAD_BYTES,
    )
    session_secret: str = Field(default="local-session-secret-change-before-sharing", min_length=32)
    session_secret_fallback: str | None = Field(default=None, min_length=32)
    cors_origins: list[str] = ["http://localhost:3000"]
    cookie_secure: bool = False

    identity_provider: Literal["local", "supabase"] = "local"
    supabase_publishable_key: str | None = None
    supabase_anon_key: str | None = None

    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    gemini_provider: Literal["disabled", "fixture", "gemini"] = "fixture"
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    cloud_storage_bucket: str | None = None
    internship_local_storage_path: Path = Path(".local/internship-uploads")
    upload_scanner_provider: Literal["disabled", "clamav"] = "disabled"
    clamav_host: str | None = None
    clamav_port: int = Field(default=3310, ge=1, le=65535)
    scan_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    outbox_stale_after_seconds: int = Field(default=2100, ge=600, le=86400)

    payment_provider: Literal["manual_external"] = "manual_external"
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
        if not self.database_url.startswith("postgresql+asyncpg://"):
            violations.append("non-PostgreSQL production database")
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            violations.append("local production database")
        if self.storage_provider != "supabase":
            violations.append("STORAGE_PROVIDER=supabase")
        if self.upload_scanner_provider != "clamav":
            violations.append("UPLOAD_SCANNER_PROVIDER=clamav")
        if not self.clamav_host:
            violations.append("missing ClamAV host")
        elif not _is_rfc1918_ipv4(self.clamav_host):
            violations.append("ClamAV host must be an RFC1918 IPv4 address")
        if self.storage_provider == "supabase":
            if not self.supabase_url:
                violations.append("missing Supabase URL")
            if not self.supabase_service_role_key:
                violations.append("missing Supabase service-role key")
            if not self.supabase_storage_bucket:
                violations.append("missing Supabase Storage bucket")
        for label, value in (("Supabase URL", self.supabase_url),):
            if value and not _is_secure_hosted_url(value):
                violations.append(f"non-HTTPS or malformed {label}")
        if self.app_process_role == "api":
            if self.identity_provider != "supabase":
                violations.append("IDENTITY_PROVIDER=supabase")
            if self.gemini_provider != "gemini":
                violations.append("GEMINI_PROVIDER=gemini")
            if self.credential_signing_provider == "demo":
                violations.append("demo credential signing")
            if not self.cookie_secure:
                violations.append("insecure cookies")
            if self.session_secret.startswith("local-"):
                violations.append("default session secret")
            if self.session_secret_fallback and self.session_secret_fallback.startswith("local-"):
                violations.append("default fallback session secret")
            if "*" in self.cors_origins:
                violations.append("wildcard CORS")
            if not (self.supabase_publishable_key or self.supabase_anon_key):
                violations.append("missing Supabase Auth publishable key")
            if not self.google_cloud_project:
                violations.append("missing Vertex AI project")
            if self.credential_signing_provider == "kms":
                if not self.credential_kms_key_name:
                    violations.append("missing KMS signing key version")
                elif (
                    re.fullmatch(
                        r"projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[^/]+/"
                        r"cryptoKeyVersions/[^/]+",
                        self.credential_kms_key_name,
                    )
                    is None
                ):
                    violations.append("invalid KMS signing key version")
            if any("localhost" in value or "127.0.0.1" in value for value in self.cors_origins):
                violations.append("local CORS origin")
            for label, value in (("web base URL", self.web_base_url),):
                if not _is_secure_hosted_url(value):
                    violations.append(f"non-HTTPS or malformed {label}")
            if any(not _is_exact_https_origin(value) for value in self.cors_origins):
                violations.append("non-HTTPS or malformed CORS origin")
        if violations:
            raise ValueError("Unsafe production configuration: " + ", ".join(violations))
        return self


def _is_secure_hosted_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.fragment
    )


def _is_exact_https_origin(value: str) -> bool:
    if not _is_secure_hosted_url(value):
        return False
    parsed = urlsplit(value)
    return parsed.path in {"", "/"} and not parsed.query


def _is_rfc1918_ipv4(value: str) -> bool:
    try:
        address = ip_address(value)
    except ValueError:
        return False
    if not isinstance(address, IPv4Address):
        return False
    return any(
        address in network
        for network in (
            IPv4Network("10.0.0.0/8"),
            IPv4Network("172.16.0.0/12"),
            IPv4Network("192.168.0.0/16"),
        )
    )


def migration_database_url(settings: Settings) -> str:
    if settings.database_pool_mode == "transaction" and not settings.database_migration_url:
        raise ValueError(
            "DATABASE_MIGRATION_URL is required when migrations target a transaction-pooled runtime"
        )
    return settings.database_migration_url or settings.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
