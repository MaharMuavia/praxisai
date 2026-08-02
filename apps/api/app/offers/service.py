import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.enums import OfferState
from app.domain.models import (
    AssignmentOffer,
    LeadProfile,
    OutboxEvent,
    Project,
    ProjectAssignment,
    StudentProfile,
)
from app.notifications.service import notification_event


class OfferError(ValueError):
    pass


async def decide_offer(
    session: AsyncSession,
    *,
    offer_id: uuid.UUID,
    principal: SessionPrincipal,
    accept: bool,
    correlation_id: uuid.UUID,
    idempotency_key: str,
) -> AssignmentOffer:
    intended_state = OfferState.ACCEPTED.value if accept else OfferState.DECLINED.value
    replay = await session.scalar(
        select(AssignmentOffer).where(AssignmentOffer.decision_idempotency_key == idempotency_key)
    )
    if replay is not None:
        if (
            replay.id != offer_id
            or replay.recipient_user_id != principal.user_id
            or replay.state != intended_state
        ):
            raise OfferError("Idempotency key was already used for another decision")
        return replay
    offer = await session.scalar(
        select(AssignmentOffer).where(AssignmentOffer.id == offer_id).with_for_update()
    )
    if offer is None or offer.recipient_user_id != principal.user_id:
        raise OfferError("Offer not found")
    if offer.state != OfferState.OFFERED.value:
        raise OfferError("Offer is no longer open")
    now = datetime.now(UTC)
    expires_at = (
        offer.expires_at
        if offer.expires_at.tzinfo is not None
        else offer.expires_at.replace(tzinfo=UTC)
    )
    if expires_at <= now:
        offer.state = OfferState.EXPIRED.value
        await session.commit()
        raise OfferError("Offer has expired; expiry does not affect reputation")
    project = await session.scalar(
        select(Project).where(Project.id == offer.project_id).with_for_update()
    )
    if project is None or project.funded_minor < project.required_deposit_minor:
        raise OfferError("Project funding is no longer confirmed")
    project_version = offer.terms_snapshot.get("project_version")
    if isinstance(project_version, int) and project.version != project_version:
        raise OfferError("Offer terms are stale because the project changed")
    if offer.role == "technical lead":
        lead = await session.scalar(
            select(LeadProfile).where(LeadProfile.user_id == principal.user_id)
        )
        if lead is None or not lead.verified or lead.committed_hours >= lead.workload_cap_hours:
            raise OfferError("Lead eligibility or capacity is no longer valid")
        if offer.terms_snapshot.get("conflict_declared") is True:
            raise OfferError("A declared lead conflict must be resolved before acceptance")
    else:
        student = await session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == principal.user_id)
        )
        if student is None or not student.eligible:
            raise OfferError("Student eligibility is no longer valid")
        offered_hours = offer.terms_snapshot.get("expected_weekly_hours", 0)
        if not isinstance(offered_hours, int) or (
            student.committed_hours + offered_hours > student.workload_cap_hours
        ):
            raise OfferError("Offer would exceed the student's workload cap")

    offer.state = intended_state
    offer.decided_at = now
    offer.decision_idempotency_key = idempotency_key
    if accept:
        session.add(
            ProjectAssignment(
                project_id=offer.project_id,
                user_id=principal.user_id,
                role=offer.role,
                offer_id=offer.id,
            )
        )
    session.add(
        OutboxEvent(
            event_type="AssignmentOfferAccepted" if accept else "AssignmentOfferDeclined",
            aggregate_type="assignment_offer",
            aggregate_id=offer.id,
            payload={"project_id": str(offer.project_id), "recipient_id": str(principal.user_id)},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=project.created_by_id,
            category="offers",
            title="Assignment offer decision",
            body=(
                "A participant accepted the assignment offer."
                if accept
                else "A participant declined the assignment offer without penalty."
            ),
            resource_path=f"/client/projects/{project.id}",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(offer)
    return offer
