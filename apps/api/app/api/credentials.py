import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import select

from app.auth.dependencies import DbSession, IdempotencyKey, Principal, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.credentials.lifecycle import (
    CredentialLifecycleError,
    CredentialNotFound,
    issue_project_credential,
    revoke_project_credential,
)
from app.credentials.service import (
    DemoSigningProvider,
    KmsSigningProvider,
    SigningProvider,
    build_verification_qr_png,
    render_credential_pdf,
    verify_signed_credential,
)
from app.domain.enums import Role
from app.domain.models import (
    Credential,
    CredentialRevocation,
)
from app.domain.schemas import CredentialIssueRequest, CredentialRevokeRequest, PublicCredential
from app.rate_limits.service import RateLimitExceeded, consume_rate_limit

router = APIRouter(tags=["credentials"])


async def _consume_public_limit(session: DbSession, request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    try:
        await consume_rate_limit(
            session,
            raw_key=f"credential:{client_host}",
            limit=60,
            window_seconds=60,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc


async def _revocation_for(
    session: DbSession, credential_id: uuid.UUID
) -> CredentialRevocation | None:
    revocation: CredentialRevocation | None = await session.scalar(
        select(CredentialRevocation).where(CredentialRevocation.credential_id == credential_id)
    )
    return revocation


def _signer(settings: Settings) -> SigningProvider:
    if settings.credential_signing_provider == "demo":
        if not (settings.is_local_or_test or settings.demo_mode):
            raise RuntimeError("Demo signing is prohibited in this environment")
        return DemoSigningProvider(settings.credential_demo_private_key_path)
    if not settings.credential_kms_key_name:
        raise RuntimeError("CREDENTIAL_KMS_KEY_NAME is required")
    return KmsSigningProvider(settings.credential_kms_key_name)


@router.post("/ops/projects/{project_id}/credentials", status_code=201)
async def issue_credential(
    project_id: uuid.UUID,
    body: CredentialIssueRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    request: Request,
) -> dict[str, object]:
    try:
        signer = _signer(settings)
        credential = await issue_project_credential(
            session,
            project_id=project_id,
            body=body,
            principal=principal,
            signer=signer,
            issuer=settings.credential_issuer,
            correlation_id=request.state.correlation_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except CredentialNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CredentialLifecycleError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return {
        "id": credential.id,
        "public_slug": credential.public_slug,
        "status": credential.status,
    }


@router.get("/public/credentials/{public_slug}", response_model=PublicCredential)
async def public_credential(
    public_slug: str,
    request: Request,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublicCredential:
    await _consume_public_limit(session, request)
    credential = await session.scalar(
        select(Credential).where(Credential.public_slug == public_slug)
    )
    if credential is None:
        return PublicCredential(status="NOT_FOUND", signature_valid=False, credential=None)
    try:
        signature_valid = verify_signed_credential(
            _signer(settings),
            credential.canonical_payload,
            credential.payload_hash,
            credential.signature,
        )
    except RuntimeError:
        signature_valid = False
    revocation = await _revocation_for(session, credential.id)
    effective_status = "REVOKED" if revocation else "VALID"
    public_payload = dict(credential.canonical_payload)
    public_payload["status"] = effective_status
    if revocation:
        public_payload["revoked_at"] = revocation.revoked_at.isoformat()
    return PublicCredential(
        status=effective_status,
        signature_valid=signature_valid,
        credential=public_payload,
        environment_label=str(public_payload.get("environment", "live")),
    )


@router.get("/public/credentials/{public_slug}/qr.png")
async def credential_qr(
    public_slug: str,
    request: Request,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    await _consume_public_limit(session, request)
    credential = await session.scalar(
        select(Credential).where(Credential.public_slug == public_slug)
    )
    if credential is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credential not found")
    verification_url = f"{settings.web_base_url.rstrip('/')}/verify/{credential.public_slug}"
    try:
        content = build_verification_qr_png(verification_url)
    except ValueError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return Response(
        content=content,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/credentials/{credential_id}/pdf")
async def credential_pdf(
    credential_id: uuid.UUID,
    principal: Principal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    credential = await session.get(Credential, credential_id)
    if credential is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credential not found")
    if principal.user_id != credential.student_user_id and principal.role not in {
        Role.COORDINATOR.value,
        Role.PLATFORM_ADMIN.value,
    }:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credential not found")
    revocation = await _revocation_for(session, credential.id)
    effective_status = "REVOKED" if revocation else "VALID"
    try:
        signature_valid = verify_signed_credential(
            _signer(settings),
            credential.canonical_payload,
            credential.payload_hash,
            credential.signature,
        )
        content = render_credential_pdf(
            payload=credential.canonical_payload,
            verification_url=(
                f"{settings.web_base_url.rstrip('/')}/verify/{credential.public_slug}"
            ),
            status=effective_status,
            signature_valid=signature_valid,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="praxis-credential-{credential.id}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )


@router.post("/ops/credentials/{credential_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_credential(
    credential_id: uuid.UUID,
    body: CredentialRevokeRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
    key: IdempotencyKey,
    request: Request,
) -> None:
    try:
        await revoke_project_credential(
            session,
            credential_id=credential_id,
            principal=principal,
            reason=body.reason,
            idempotency_key=key,
            correlation_id=request.state.correlation_id,
        )
    except CredentialNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CredentialLifecycleError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
