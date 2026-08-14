import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

import httpx
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.domain.models import OrganizationMembership, User


@dataclass(frozen=True)
class Identity:
    subject: str
    email: str


class IdentityProvider(Protocol):
    async def verify(self, token: str) -> Identity: ...


class IdentityLinkConflict(ValueError):
    """The verified identity conflicts with an existing account binding."""


class SupabaseIdentityProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url:
            raise ValueError("Supabase URL is not configured")
        auth_key = settings.supabase_publishable_key or settings.supabase_anon_key
        if not auth_key:
            raise ValueError("Supabase Auth publishable key is not configured")
        self._url = settings.supabase_url.rstrip("/")
        self._auth_key = auth_key

    async def verify(self, token: str) -> Identity:
        if len(token) < 20:
            raise ValueError("Invalid Supabase access token")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self._url}/auth/v1/user",
                    headers={
                        "apikey": self._auth_key,
                        "Authorization": f"Bearer {token}",
                    },
                )
        except httpx.HTTPError as exc:
            raise ValueError("Supabase authentication is unavailable") from exc
        if response.status_code != 200:
            raise ValueError("Invalid or expired Supabase identity")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("Supabase returned malformed identity data") from exc
        subject = payload.get("id")
        email = payload.get("email")
        confirmed_at = payload.get("email_confirmed_at") or payload.get("confirmed_at")
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or not isinstance(email, str)
            or not email.strip()
        ):
            raise ValueError("Supabase identity is missing a user ID or email")
        if not confirmed_at:
            raise ValueError("Supabase identity email is not verified")
        return Identity(subject=subject.strip(), email=email.strip().casefold())


async def resolve_or_link_identity_user(
    session: AsyncSession,
    identity: Identity,
) -> User | None:
    """Resolve a Supabase identity without allowing email to override a binding.

    The immutable provider subject is authoritative. Email matching is only a
    one-time bridge for an existing account that has never been bound to an
    external identity.
    """

    subject = identity.subject.strip()
    email = identity.email.strip().casefold()
    if not subject or not email:
        raise IdentityLinkConflict("Verified identity is missing a subject or email")

    subject_user = await session.scalar(
        select(User).where(User.external_subject == subject).with_for_update()
    )
    email_users = list(
        (
            await session.scalars(
                select(User).where(func.lower(User.email) == email).with_for_update()
            )
        ).all()
    )
    if len(email_users) > 1:
        raise IdentityLinkConflict("Multiple accounts use the verified email")
    email_user = email_users[0] if email_users else None

    if subject_user is not None:
        if email_user is not None and email_user.id != subject_user.id:
            raise IdentityLinkConflict("Verified subject and email belong to different accounts")
        if subject_user.email != email:
            subject_user.email = email
        user = subject_user
    elif email_user is None:
        return None
    else:
        if email_user.external_subject is not None:
            raise IdentityLinkConflict("Verified email is already bound to another identity")
        email_user.external_subject = subject
        if email_user.email != email:
            email_user.email = email
        user = email_user

    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise IdentityLinkConflict("Verified identity conflicts with an existing account") from exc
    return user


@dataclass(frozen=True)
class SessionPrincipal:
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str


class SessionCodec:
    def __init__(self, secret: str, fallback_secret: str | None = None) -> None:
        self._secrets = tuple(
            value.encode() for value in (secret, fallback_secret) if value is not None
        )

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
        signature = hmac.new(self._secrets[0], body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    def decode(self, token: str) -> SessionPrincipal:
        try:
            body, supplied = token.rsplit(".", 1)
            valid_signature = False
            for secret in self._secrets:
                expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
                valid_signature |= hmac.compare_digest(supplied, expected)
            if not valid_signature:
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
