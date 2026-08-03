import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import AuditEvent, PublicIntakeSubmission
from app.domain.schemas import PublicIntakeSubmissionCreate, PublicIntakeSubmissionUpdate


async def create_submission(
    session: AsyncSession,
    *,
    body: PublicIntakeSubmissionCreate,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    existing = await session.scalar(
        select(PublicIntakeSubmission).where(
            PublicIntakeSubmission.idempotency_key == idempotency_key
        )
    )
    if existing is not None:
        return existing

    payload = body.model_dump(
        mode="json",
        exclude={
            "kind",
            "full_name",
            "email",
            "country",
            "consent",
            "source",
            "campaign",
            "honeypot",
        },
    )
    payload["full_name"] = body.full_name.strip()
    payload["country"] = body.country.strip()
    submission = PublicIntakeSubmission(
        kind=body.kind,
        contact_email=body.email.strip().lower(),
        source=body.source.strip() if body.source else None,
        campaign=body.campaign.strip() if body.campaign else None,
        payload=payload,
        consent_snapshot={
            "granted": True,
            "version": "public-intake-v1",
            "captured_at": datetime.now(UTC).isoformat(),
        },
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
    session.add(submission)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=None,
            organization_id=None,
            action="public_intake.submitted",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={"kind": body.kind, "source": body.source, "campaign": body.campaign},
        )
    )
    await session.commit()
    await session.refresh(submission)
    return submission


async def list_submissions(
    session: AsyncSession, *, status: str | None, limit: int
) -> list[PublicIntakeSubmission]:
    query = (
        select(PublicIntakeSubmission)
        .order_by(PublicIntakeSubmission.created_at.desc())
        .limit(limit)
    )
    if status:
        query = query.where(PublicIntakeSubmission.status == status)
    return list((await session.scalars(query)).all())


async def update_submission(
    session: AsyncSession,
    *,
    submission_id: uuid.UUID,
    body: PublicIntakeSubmissionUpdate,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    submission = await session.get(PublicIntakeSubmission, submission_id)
    if submission is None:
        raise LookupError("Intake submission not found")
    submission.status = body.status
    submission.owner_id = body.owner_id
    submission.qualification_notes = body.qualification_notes
    submission.rejection_reason = body.rejection_reason
    submission.reviewed_at = datetime.now(UTC)
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="public_intake.reviewed",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={
                "status": body.status,
                "owner_id": str(body.owner_id) if body.owner_id else None,
            },
        )
    )
    await session.commit()
    await session.refresh(submission)
    return submission
