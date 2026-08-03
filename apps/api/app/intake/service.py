import base64
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    Organization,
    OrganizationMembership,
    PublicIntakeIdempotency,
    PublicIntakeSubmission,
    User,
)
from app.domain.schemas import PublicIntakeSubmissionCreate, PublicIntakeSubmissionUpdate


class IdempotencyConflict(ValueError):
    pass


class InvalidIntakeTransition(ValueError):
    pass


class IntakeVersionConflict(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "NEW": {"IN_REVIEW", "REJECTED"},
    "IN_REVIEW": {"QUALIFIED", "REJECTED"},
    "QUALIFIED": {"CONVERTED", "REJECTED"},
    "REJECTED": {"IN_REVIEW"},
    "CONVERTED": set(),
}


def submission_payload_hash(body: PublicIntakeSubmissionCreate) -> str:
    canonical = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


async def find_submission(
    session: AsyncSession, *, idempotency_key: str
) -> PublicIntakeSubmission | None:
    result = await session.scalars(
        select(PublicIntakeSubmission).where(
            PublicIntakeSubmission.idempotency_key == idempotency_key
        )
    )
    return result.first()


def ensure_idempotency_matches(
    submission: PublicIntakeSubmission, *, payload_hash: str
) -> PublicIntakeSubmission:
    if submission.payload_hash and submission.payload_hash != payload_hash:
        raise IdempotencyConflict("Idempotency-Key was already used for different content")
    return submission


async def reserve_idempotency(
    session: AsyncSession,
    *,
    idempotency_key: str,
    payload_hash: str,
    kind: str,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission | None:
    """Reserve a key before rate limiting so retries cannot consume another quota slot."""
    existing = await session.scalar(
        select(PublicIntakeIdempotency).where(
            PublicIntakeIdempotency.idempotency_key == idempotency_key
        )
    )
    if existing is not None:
        if existing.payload_hash != payload_hash:
            raise IdempotencyConflict("Idempotency-Key was already used for different content")
        if existing.status == "COMPLETED" and existing.submission_id:
            submission = await session.get(PublicIntakeSubmission, existing.submission_id)
            if submission is not None:
                return submission
        if existing.status == "FAILED":
            existing.status = "RESERVED"
            existing.correlation_id = correlation_id
            await session.commit()
            return None
        raise IdempotencyConflict("A submission with this Idempotency-Key is still being processed")

    reservation = PublicIntakeIdempotency(
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        kind=kind,
        status="RESERVED",
        correlation_id=correlation_id,
    )
    session.add(reservation)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        existing = await session.scalar(
            select(PublicIntakeIdempotency).where(
                PublicIntakeIdempotency.idempotency_key == idempotency_key
            )
        )
        if existing is None:
            raise exc
        if existing.payload_hash != payload_hash:
            raise IdempotencyConflict(
                "Idempotency-Key was already used for different content"
            ) from exc
        if existing.status == "COMPLETED" and existing.submission_id:
            return await session.get(PublicIntakeSubmission, existing.submission_id)
        raise IdempotencyConflict(
            "A submission with this Idempotency-Key is still being processed"
        ) from exc
    return None


async def mark_idempotency_failed(session: AsyncSession, *, idempotency_key: str) -> None:
    await session.rollback()
    reservation = await session.scalar(
        select(PublicIntakeIdempotency).where(
            PublicIntakeIdempotency.idempotency_key == idempotency_key
        )
    )
    if reservation is not None and reservation.status != "COMPLETED":
        reservation.status = "FAILED"
        await session.commit()


async def _complete_idempotency(
    session: AsyncSession, *, idempotency_key: str, submission_id: uuid.UUID
) -> None:
    reservation = await session.scalar(
        select(PublicIntakeIdempotency).where(
            PublicIntakeIdempotency.idempotency_key == idempotency_key
        )
    )
    if reservation is not None:
        reservation.status = "COMPLETED"
        reservation.submission_id = submission_id


async def create_submission(
    session: AsyncSession,
    *,
    body: PublicIntakeSubmissionCreate,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    payload_hash = submission_payload_hash(body)
    existing = await find_submission(session, idempotency_key=idempotency_key)
    if existing is not None:
        return ensure_idempotency_matches(existing, payload_hash=payload_hash)

    now = datetime.now(UTC)
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
            "granted": body.consent is True,
            "version": "public-intake-v1",
            "captured_at": now.isoformat(),
            "purpose": "review_and_pathway_contact",
        },
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        payload_hash=payload_hash,
        retention_expires_at=now + timedelta(days=180),
    )
    session.add(submission)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        existing = await find_submission(session, idempotency_key=idempotency_key)
        if existing is None:
            raise exc
        return ensure_idempotency_matches(existing, payload_hash=payload_hash)

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
    await _complete_idempotency(
        session, idempotency_key=idempotency_key, submission_id=submission.id
    )
    await session.commit()
    await session.refresh(submission)
    return submission


def _cursor_value(value: datetime, submission_id: uuid.UUID) -> str:
    raw = json.dumps({"created_at": value.isoformat(), "id": str(submission_id)}).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded).decode())
        return datetime.fromisoformat(value["created_at"]), uuid.UUID(value["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid intake queue cursor") from exc


async def list_submission_summaries(
    session: AsyncSession,
    *,
    status: str | None,
    kind: str | None,
    owner_id: uuid.UUID | None,
    source: str | None,
    search: str | None,
    action_required: bool | None,
    cursor: str | None,
    page_size: int,
) -> tuple[list[PublicIntakeSubmission], str | None]:
    query = select(PublicIntakeSubmission).where(
        PublicIntakeSubmission.deleted_at.is_(None),
        PublicIntakeSubmission.anonymized_at.is_(None),
    )
    if status:
        query = query.where(PublicIntakeSubmission.status == status)
    if kind:
        query = query.where(PublicIntakeSubmission.kind == kind)
    if owner_id:
        query = query.where(PublicIntakeSubmission.owner_id == owner_id)
    if source:
        query = query.where(PublicIntakeSubmission.source == source)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                PublicIntakeSubmission.payload["full_name"].as_string().ilike(pattern),
                PublicIntakeSubmission.source.ilike(pattern),
                PublicIntakeSubmission.campaign.ilike(pattern),
            )
        )
    if action_required is True:
        query = query.where(PublicIntakeSubmission.status.in_(["NEW", "IN_REVIEW"]))
    if cursor:
        created_at, submission_id = decode_cursor(cursor)
        query = query.where(
            or_(
                PublicIntakeSubmission.created_at < created_at,
                and_(
                    PublicIntakeSubmission.created_at == created_at,
                    PublicIntakeSubmission.id < submission_id,
                ),
            )
        )
    rows = list(
        (
            await session.scalars(
                query.order_by(
                    PublicIntakeSubmission.created_at.desc(), PublicIntakeSubmission.id.desc()
                ).limit(page_size + 1)
            )
        ).all()
    )
    next_cursor = (
        _cursor_value(rows[page_size - 1].created_at, rows[page_size - 1].id)
        if len(rows) > page_size
        else None
    )
    return rows[:page_size], next_cursor


async def get_submission(
    session: AsyncSession, *, submission_id: uuid.UUID
) -> PublicIntakeSubmission:
    submission = await session.get(PublicIntakeSubmission, submission_id)
    if submission is None or submission.deleted_at is not None:
        raise LookupError("Intake submission not found")
    return submission


async def _validate_owner(session: AsyncSession, owner_id: uuid.UUID | None) -> None:
    if owner_id is None:
        return
    owner = await session.scalar(
        select(User)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            and_(
                User.id == owner_id,
                User.is_active.is_(True),
                OrganizationMembership.is_active.is_(True),
                OrganizationMembership.role.in_(("coordinator", "platform_admin")),
                Organization.kind == "internal",
            )
        )
    )
    if owner is None:
        raise ValueError("Owner must be an active operations coordinator")


def allowed_transitions(submission: PublicIntakeSubmission) -> list[str]:
    if submission.deleted_at or submission.anonymized_at or submission.withdrawal_requested_at:
        return []
    return sorted(_ALLOWED_TRANSITIONS.get(submission.status, set()))


def _validate_transition(
    submission: PublicIntakeSubmission, body: PublicIntakeSubmissionUpdate
) -> None:
    if body.status != submission.status and body.status not in _ALLOWED_TRANSITIONS.get(
        submission.status, set()
    ):
        raise InvalidIntakeTransition(
            f"Cannot move intake from {submission.status} to {body.status}"
        )
    if body.status == "REJECTED" and not body.rejection_reason:
        raise InvalidIntakeTransition("A rejection reason is required")
    if body.status == "QUALIFIED" and not body.qualification_notes:
        raise InvalidIntakeTransition("Qualification notes are required")
    if body.status == "CONVERTED" and not body.conversion_evidence:
        raise InvalidIntakeTransition("Conversion evidence is required")
    if submission.status == "REJECTED" and body.status == "IN_REVIEW" and not body.reopen_reason:
        raise InvalidIntakeTransition("A reopen reason is required")


async def update_submission(
    session: AsyncSession,
    *,
    submission_id: uuid.UUID,
    body: PublicIntakeSubmissionUpdate,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    submission = await session.scalar(
        select(PublicIntakeSubmission)
        .where(PublicIntakeSubmission.id == submission_id)
        .with_for_update()
    )
    if submission is None or submission.deleted_at is not None:
        raise LookupError("Intake submission not found")
    if submission.anonymized_at or submission.withdrawal_requested_at:
        raise InvalidIntakeTransition("Privacy-terminal intake records cannot be reviewed")
    if submission.version != body.expected_version:
        raise IntakeVersionConflict("This intake record changed; reload before updating")
    _validate_transition(submission, body)
    await _validate_owner(session, body.owner_id)

    old_status = submission.status
    old_owner_id = submission.owner_id
    submission.status = body.status
    submission.owner_id = body.owner_id
    submission.qualification_notes = body.qualification_notes
    submission.rejection_reason = body.rejection_reason
    submission.conversion_evidence = body.conversion_evidence
    submission.reviewed_at = datetime.now(UTC)
    submission.version += 1
    if body.status == "REJECTED":
        submission.retention_expires_at = datetime.now(UTC) + timedelta(days=30)
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="public_intake.reviewed",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={
                "from_status": old_status,
                "status": body.status,
                "from_owner_id": str(old_owner_id) if old_owner_id else None,
                "owner_id": str(body.owner_id) if body.owner_id else None,
                "version": submission.version,
                "reason": body.reopen_reason or body.rejection_reason,
            },
        )
    )
    await session.commit()
    await session.refresh(submission)
    return submission


def _redact_submission(submission: PublicIntakeSubmission, now: datetime) -> None:
    submission.contact_email = None
    submission.source = None
    submission.campaign = None
    submission.owner_id = None
    submission.qualification_notes = None
    submission.rejection_reason = None
    submission.conversion_evidence = None
    submission.payload = {"redacted": True, "kind": submission.kind}
    submission.consent_snapshot = {"redacted": True}
    submission.anonymized_at = now
    submission.withdrawal_requested_at = submission.withdrawal_requested_at or now


async def anonymize_expired_submissions(session: AsyncSession, *, now: datetime) -> int:
    rows = list(
        (
            await session.scalars(
                select(PublicIntakeSubmission)
                .where(
                    PublicIntakeSubmission.retention_expires_at <= now,
                    PublicIntakeSubmission.anonymized_at.is_(None),
                    PublicIntakeSubmission.deleted_at.is_(None),
                )
                .with_for_update(skip_locked=True)
            )
        ).all()
    )
    for submission in rows:
        _redact_submission(submission, now)
    await session.commit()
    return len(rows)


async def anonymize_submission(
    session: AsyncSession,
    *,
    submission_id: uuid.UUID,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    submission = await get_submission(session, submission_id=submission_id)
    if submission.anonymized_at:
        return submission
    now = datetime.now(UTC)
    _redact_submission(submission, now)
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="public_intake.anonymized",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={"reason": "privacy_retention_request", "anonymized_at": now.isoformat()},
        )
    )
    await session.commit()
    await session.refresh(submission)
    return submission


async def request_withdrawal(
    session: AsyncSession,
    *,
    submission_id: uuid.UUID,
    principal: SessionPrincipal,
    reason: str,
    correlation_id: uuid.UUID,
) -> PublicIntakeSubmission:
    submission = await get_submission(session, submission_id=submission_id)
    if submission.anonymized_at:
        return submission
    submission.withdrawal_requested_at = submission.withdrawal_requested_at or datetime.now(UTC)
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="public_intake.withdrawal_requested",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={"reason": reason},
        )
    )
    await session.commit()
    await session.refresh(submission)
    return submission


async def delete_submission(
    session: AsyncSession,
    *,
    submission_id: uuid.UUID,
    principal: SessionPrincipal,
    reason: str,
    correlation_id: uuid.UUID,
) -> None:
    submission = await get_submission(session, submission_id=submission_id)
    now = datetime.now(UTC)
    _redact_submission(submission, now)
    submission.deleted_at = now
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="public_intake.deleted",
            resource_type="public_intake_submission",
            resource_id=submission.id,
            correlation_id=correlation_id,
            payload={"reason": reason},
        )
    )
    await session.commit()


async def list_owners(session: AsyncSession) -> list[User]:
    return list(
        (
            await session.scalars(
                select(User)
                .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
                .join(Organization, Organization.id == OrganizationMembership.organization_id)
                .where(
                    User.is_active.is_(True),
                    OrganizationMembership.is_active.is_(True),
                    OrganizationMembership.role.in_(("coordinator", "platform_admin")),
                    Organization.kind == "internal",
                )
                .order_by(User.display_name)
            )
        ).all()
    )


async def list_audit_events(session: AsyncSession, *, submission_id: uuid.UUID) -> list[AuditEvent]:
    return list(
        (
            await session.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.resource_type == "public_intake_submission",
                    AuditEvent.resource_id == submission_id,
                )
                .order_by(AuditEvent.created_at.asc())
            )
        ).all()
    )
