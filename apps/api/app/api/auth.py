from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select

from app.auth.capabilities import INTERNSHIP_CAPABILITIES
from app.auth.dependencies import DbSession, Principal
from app.auth.service import (
    IdentityLinkConflict,
    SessionCodec,
    SessionPrincipal,
    SupabaseIdentityProvider,
    new_csrf_token,
    resolve_or_link_identity_user,
)
from app.config import Settings, get_settings
from app.domain.models import Notification, Organization, OrganizationMembership, User
from app.domain.schemas import (
    LocalSessionRequest,
    MembershipView,
    SessionView,
    SupabaseSessionRequest,
)
from app.rate_limits.service import (
    RateLimitExceeded,
    consume_rate_limit,
    opaque_rate_limit_key,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
AUTH_GLOBAL_RATE_LIMIT = 300
AUTH_LOCAL_USER_RATE_LIMIT = 20
AUTH_SUPABASE_TOKEN_RATE_LIMIT = 10
AUTH_SUPABASE_SUBJECT_RATE_LIMIT = 10

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
        "internships:apply",
        "internships:view_own",
        "internships:participate",
        "internships:submit",
        "internships:request_extension",
    ],
    "technical_lead": [
        "offers:decide",
        "plans:review",
        "release:recommend",
        "work:view",
        "internships:review",
    ],
    "reviewer": ["internships:review"],
    "coordinator": [
        "projects:operate",
        "approvals:decide",
        "staffing:approve",
        "payouts:approve",
        "internships:review",
        "internships:manage_content",
        "internships:manage_cohort",
        "internships:decide_application",
        "internships:decide_completion",
        "internships:issue_certificate",
        "internships:view_analytics",
    ],
    "university_viewer": ["university:aggregate:view", "university:consented:view"],
    "platform_admin": [
        "platform:configure",
        "jobs:retry",
        "access:manage",
        "internships:review",
        "internships:manage_content",
        "internships:manage_cohort",
        "internships:decide_application",
        "internships:decide_completion",
        "internships:issue_certificate",
        "internships:view_analytics",
    ],
}

for _role, _capabilities in INTERNSHIP_CAPABILITIES.items():
    CAPABILITIES[_role] = sorted(set(CAPABILITIES.get(_role, [])) | set(_capabilities))


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


async def _enforce_auth_rate_limit(
    session: DbSession,
    *,
    raw_key: str,
    limit: int,
) -> None:
    try:
        await consume_rate_limit(
            session,
            raw_key=raw_key,
            limit=limit,
            window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc


@router.post("/local/session", status_code=status.HTTP_204_NO_CONTENT)
async def local_session(
    body: LocalSessionRequest,
    response: Response,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not (settings.is_local_or_test or settings.demo_mode):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    await _enforce_auth_rate_limit(
        session,
        raw_key="auth:local:global",
        limit=AUTH_GLOBAL_RATE_LIMIT,
    )
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
    await _enforce_auth_rate_limit(
        session,
        raw_key=opaque_rate_limit_key(
            namespace="auth:local:user",
            identifier=str(membership.user_id),
        ),
        limit=AUTH_LOCAL_USER_RATE_LIMIT,
    )
    await _set_session(
        response,
        SessionPrincipal(body.user_id, body.organization_id, body.role),
        settings,
    )


@router.post("/session", status_code=status.HTTP_204_NO_CONTENT)
async def supabase_session(
    body: SupabaseSessionRequest,
    response: Response,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if settings.identity_provider != "supabase":
        raise HTTPException(status.HTTP_409_CONFLICT, "Supabase identity is not configured")
    await _enforce_auth_rate_limit(
        session,
        raw_key=opaque_rate_limit_key(
            namespace="auth:supabase:token",
            identifier=body.access_token,
        ),
        limit=AUTH_SUPABASE_TOKEN_RATE_LIMIT,
    )
    await _enforce_auth_rate_limit(
        session,
        raw_key="auth:supabase:global",
        limit=AUTH_GLOBAL_RATE_LIMIT,
    )
    try:
        identity = await SupabaseIdentityProvider(settings).verify(body.access_token)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    await _enforce_auth_rate_limit(
        session,
        raw_key=opaque_rate_limit_key(
            namespace="auth:supabase:subject",
            identifier=identity.subject,
        ),
        limit=AUTH_SUPABASE_SUBJECT_RATE_LIMIT,
    )
    try:
        user = await resolve_or_link_identity_user(session, identity)
    except IdentityLinkConflict as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Supabase identity conflicts with an existing account",
        ) from exc
    if user is None:
        await session.rollback()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No PraxisAI account is linked")
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if membership is None or not user.is_active:
        await session.rollback()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No active workspace membership")
    await session.commit()
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
