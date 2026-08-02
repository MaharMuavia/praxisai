import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

from firebase_admin import auth, credentials, initialize_app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.domain.models import OrganizationMembership, User


@dataclass(frozen=True)
class Identity:
    subject: str
    email: str


class IdentityProvider(Protocol):
    async def verify(self, token: str) -> Identity: ...


class FirebaseIdentityProvider:
    def __init__(self, settings: Settings) -> None:
        self._project_id = settings.firebase_project_id
        options = (
            {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        )
        credential = None
        if settings.firebase_credentials_json:
            if not settings.is_local_or_test:
                raise ValueError(
                    "Explicit credentials JSON is allowed only in local or test environments"
                )
            credential = credentials.Certificate(json.loads(settings.firebase_credentials_json))

        try:
            initialize_app(credential, options)
        except ValueError:
            pass

    async def verify(self, token: str) -> Identity:
        if not self._project_id:
            raise ValueError("Firebase project ID is not configured")
        decoded = auth.verify_id_token(token, check_revoked=True)

        # Audience validation (must match expected project ID)
        aud = decoded.get("aud")
        if aud != self._project_id:
            raise ValueError(
                f"Cross-project identity rejected: expected audience '{self._project_id}', "
                f"got '{aud}'"
            )

        # Issuer validation
        expected_iss = f"https://securetoken.google.com/{self._project_id}"
        iss = decoded.get("iss")
        if iss != expected_iss:
            raise ValueError(f"Invalid identity issuer: expected '{expected_iss}', got '{iss}'")

        # Expiry check
        exp = decoded.get("exp")
        if not exp or int(exp) <= int(time.time()):
            raise ValueError("The identity token has expired")

        # Verified email check
        email = decoded.get("email")
        email_verified = decoded.get("email_verified", False)
        if not isinstance(email, str) or not email_verified:
            raise ValueError("The identity token has no verified email")

        uid = decoded.get("uid")
        if not uid or not isinstance(uid, str):
            raise ValueError("The identity token missing valid user identifier")

        return Identity(subject=uid, email=email)


@dataclass(frozen=True)
class SessionPrincipal:
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str


class SessionCodec:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def encode(self, principal: SessionPrincipal, ttl_seconds: int = 28_800) -> str:
        payload = {
            "user_id": str(principal.user_id),
            "organization_id": str(principal.organization_id),
            "role": principal.role,
            "exp": int(time.time()) + ttl_seconds,
        }
        body = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode()
        signature = hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    def decode(self, token: str) -> SessionPrincipal:
        try:
            body, supplied = token.rsplit(".", 1)
            expected = hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(supplied, expected):
                raise ValueError("invalid signature")
            payload = json.loads(base64.urlsafe_b64decode(body.encode()))
            if int(payload["exp"]) <= int(time.time()):
                raise ValueError("expired")
            return SessionPrincipal(
                user_id=uuid.UUID(payload["user_id"]),
                organization_id=uuid.UUID(payload["organization_id"]),
                role=str(payload["role"]),
            )
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid or expired session") from exc


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def validate_membership(session: AsyncSession, principal: SessionPrincipal) -> None:
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == principal.user_id,
            OrganizationMembership.organization_id == principal.organization_id,
            OrganizationMembership.role == principal.role,
            OrganizationMembership.is_active.is_(True),
        )
    )
    user = await session.get(User, principal.user_id)
    if membership is None or user is None or not user.is_active:
        raise ValueError("Session membership is no longer active")
