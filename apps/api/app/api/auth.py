from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select

from app.auth.dependencies import DbSession, Principal
from app.auth.service import (
    FirebaseIdentityProvider,
    SessionCodec,
    SessionPrincipal,
    new_csrf_token,
)
from app.config import Settings, get_settings
from app.domain.models import Notification, Organization, OrganizationMembership, User
from app.domain.schemas import (
    FirebaseSessionRequest,
    LocalSessionRequest,
    MembershipView,
    SessionView,
)
from app.rate_limits.service import RateLimitExceeded, consume_rate_limit

router = APIRouter(prefix="/auth", tags=["authentication"])

CAPABILITIES: dict[str, list[str]] = {
    "client_owner": [
        "projects:create",
        "projects:approve",
        "opportunities:publish",
        "proposals:decide",
        "payments:view",
        "members:manage",
    ],
    "client_member": ["projects:view", "projects:comment"],
    "student": [
        "learning:participate",
        "opportunities:view",
        "proposals:create",
        "offers:decide",
        "work:submit",
        "appeals:create",
        "credentials:view",
    ],
    "technical_lead": ["offers:decide", "plans:review", "release:recommend", "work:view"],
    "coordinator": ["projects:operate", "approvals:decide", "staffing:approve", "payouts:approve"],
    "university_viewer": ["university:aggregate:view", "university:consented:view"],
    "platform_admin": ["platform:configure", "jobs:retry", "access:manage"],
}


async def _set_session(
    response: Response,
    principal: SessionPrincipal,
    settings: Settings,
) -> None:
    token = SessionCodec(settings.session_secret).encode(principal)
    csrf = new_csrf_token()
    response.set_cookie(
        "praxis_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=28_800,
    )
    response.set_cookie(
        "praxis_csrf",
        csrf,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=28_800,
    )


@router.post("/local/session", status_code=status.HTTP_204_NO_CONTENT)
async def local_session(
    body: LocalSessionRequest,
    request: Request,
    response: Response,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not (settings.is_local_or_test or settings.demo_mode):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    client_host = request.client.host if request.client else "unknown"
    try:
        await consume_rate_limit(
            session, raw_key=f"auth:local:{client_host}", limit=20, window_seconds=60
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == body.user_id,
            OrganizationMembership.organization_id == body.organization_id,
            OrganizationMembership.role == body.role,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Membership is not active")
    await _set_session(
        response,
        SessionPrincipal(body.user_id, body.organization_id, body.role),
        settings,
    )


@router.post("/session", status_code=status.HTTP_204_NO_CONTENT)
async def firebase_session(
    body: FirebaseSessionRequest,
    request: Request,
    response: Response,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if settings.identity_provider != "firebase":
        raise HTTPException(status.HTTP_409_CONFLICT, "Firebase identity is not configured")
    client_host = request.client.host if request.client else "unknown"
    try:
        await consume_rate_limit(
            session, raw_key=f"auth:firebase:{client_host}", limit=10, window_seconds=60
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc
    try:
        identity = await FirebaseIdentityProvider(settings).verify(body.id_token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    user = await session.scalar(
        select(User).where(
            (User.external_subject == identity.subject) | (User.email == identity.email)
        )
    )
    if user is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No PraxisAI account is linked")
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No active workspace membership")
    await _set_session(
        response,
        SessionPrincipal(user.id, membership.organization_id, membership.role),
        settings,
    )


@router.get("/me", response_model=SessionView)
async def me(
    principal: Principal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionView:
    user = await session.get(User, principal.user_id)
    organization = await session.get(Organization, principal.organization_id)
    if user is None or organization is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session resources no longer exist")
    notification_count = await session.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id, Notification.read_at.is_(None)
        )
    )
    return SessionView(
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
        active_membership=MembershipView(
            organization_id=organization.id,
            organization_name=organization.name,
            role=principal.role,
        ),
        capabilities=CAPABILITIES.get(principal.role, []),
        onboarding_state="complete",
        notification_count=notification_count or 0,
        environment_label="demo" if settings.demo_mode else settings.app_env,
        required_consent_versions={"terms": "demo-1", "privacy": "demo-1"},
    )


@router.get("/memberships", response_model=list[MembershipView])
async def memberships(principal: Principal, session: DbSession) -> list[MembershipView]:
    rows = (
        await session.execute(
            select(OrganizationMembership, Organization)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .where(
                OrganizationMembership.user_id == principal.user_id,
                OrganizationMembership.is_active.is_(True),
            )
        )
    ).all()
    return [
        MembershipView(organization_id=org.id, organization_name=org.name, role=item.role)
        for item, org in rows
    ]


@router.post("/select-workspace", status_code=status.HTTP_204_NO_CONTENT)
async def select_workspace(
    body: LocalSessionRequest,
    response: Response,
    principal: Principal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if body.user_id != principal.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot select another user's workspace")
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == body.user_id,
            OrganizationMembership.organization_id == body.organization_id,
            OrganizationMembership.role == body.role,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Membership is not active")
    await _set_session(
        response, SessionPrincipal(body.user_id, body.organization_id, body.role), settings
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie("praxis_session")
    response.delete_cookie("praxis_csrf")


@router.get("/demo-users")
async def demo_users(
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[dict[str, object]]:
    if not (settings.is_local_or_test or settings.demo_mode):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    rows = (
        await session.execute(
            select(User, OrganizationMembership, Organization)
            .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .where(User.is_demo.is_(True), OrganizationMembership.is_active.is_(True))
            .order_by(User.display_name)
        )
    ).all()
    return [
        {
            "user_id": user.id,
            "display_name": user.display_name,
            "organization_id": membership.organization_id,
            "organization_name": organization.name,
            "role": membership.role,
        }
        for user, membership, organization in rows
    ]
