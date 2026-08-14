import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.capabilities import role_has_capability
from app.auth.service import SessionCodec, SessionPrincipal, validate_membership
from app.config import Settings, get_settings
from app.db import get_session
from app.domain.enums import Role


async def current_principal(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    praxis_session: Annotated[str | None, Cookie()] = None,
) -> SessionPrincipal:
    if praxis_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    try:
        principal = SessionCodec(
            settings.session_secret,
            settings.session_secret_fallback,
        ).decode(praxis_session)
        await validate_membership(session, principal)
        request.state.principal = principal
        return principal
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


Principal = Annotated[SessionPrincipal, Depends(current_principal)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def require_roles(*roles: Role) -> Callable[..., Coroutine[Any, Any, SessionPrincipal]]:
    async def dependency(principal: Principal) -> SessionPrincipal:
        if principal.role not in {role.value for role in roles}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Capability denied")
        return principal

    return dependency


def require_capability(
    capability: str,
) -> Callable[..., Coroutine[Any, Any, SessionPrincipal]]:
    async def dependency(principal: Principal) -> SessionPrincipal:
        if not role_has_capability(principal.role, capability):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Capability denied")
        return principal

    return dependency


async def idempotency_key(
    value: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str:
    if value is None or not 8 <= len(value) <= 128:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A valid Idempotency-Key is required")
    return value


IdempotencyKey = Annotated[str, Depends(idempotency_key)]


def correlation_id(request: Request) -> uuid.UUID:
    value = getattr(request.state, "correlation_id", None)
    return value if isinstance(value, uuid.UUID) else uuid.uuid4()
