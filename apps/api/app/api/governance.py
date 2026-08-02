import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.projects import _accessible_project
from app.auth.dependencies import DbSession, Principal, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import Appeal, AuditEvent, OutboxEvent, ReputationEvent
from app.domain.schemas import AppealCreate, AppealResolve, ReputationEventCreate
from app.notifications.service import notification_event

router = APIRouter(tags=["appeals and reputation"])


@router.get("/appeals")
async def list_appeals(principal: Principal, session: DbSession) -> list[dict[str, object]]:
    query = select(Appeal).order_by(Appeal.created_at.desc())
    if principal.role not in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        query = query.where(Appeal.appellant_id == principal.user_id)
    rows = list((await session.scalars(query)).all())
    return [
        {
            "id": item.id,
            "project_id": item.project_id,
            "decision_type": item.decision_type,
            "state": item.state,
            "reviewer_id": item.reviewer_id,
            "resolution_reason": item.resolution_reason,
            "created_at": item.created_at,
        }
        for item in rows
    ]


@router.post("/appeals", status_code=201)
async def create_appeal(
    body: AppealCreate, principal: Principal, session: DbSession
) -> dict[str, object]:
    await _accessible_project(session, principal, body.project_id)
    decided_at = body.decision_snapshot.get("decided_at")
    if not isinstance(decided_at, str):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Decision timestamp is required")
    try:
        decision_time = datetime.fromisoformat(decided_at)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid decision timestamp"
        ) from exc
    if decision_time.tzinfo is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Decision timestamp must include timezone"
        )
    if datetime.now(UTC) - decision_time.astimezone(UTC) > timedelta(days=14):
        raise HTTPException(status.HTTP_409_CONFLICT, "Appeal window has expired")
    appeal = Appeal(
        appellant_id=principal.user_id,
        project_id=body.project_id,
        decision_type=body.decision_type,
        decision_id=body.decision_id,
        state="OPEN",
        decision_snapshot=body.decision_snapshot,
    )
    session.add(appeal)
    await session.flush()
    session.add(
        OutboxEvent(
            event_type="AppealOpened",
            aggregate_type="appeal",
            aggregate_id=appeal.id,
            payload={"appeal_id": str(appeal.id), "project_id": str(appeal.project_id)},
        )
    )
    await session.commit()
    return {"id": appeal.id, "state": appeal.state}


@router.post("/ops/appeals/{appeal_id}/resolve")
async def resolve_appeal(
    appeal_id: uuid.UUID,
    body: AppealResolve,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
    request: Request,
) -> dict[str, object]:
    appeal = await session.get(Appeal, appeal_id, with_for_update=True)
    if appeal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appeal not found")
    original_actor = appeal.decision_snapshot.get("actor_id")
    if appeal.appellant_id == principal.user_id or original_actor == str(principal.user_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Reviewer has a conflict of interest")
    if appeal.state in {"UPHELD", "OVERTURNED", "PARTIALLY_OVERTURNED", "CLOSED"}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Appeal is already resolved")
    appeal.state = body.decision
    appeal.reviewer_id = principal.user_id
    appeal.resolution_reason = body.reason
    if body.decision in {"OVERTURNED", "PARTIALLY_OVERTURNED"}:
        events = list(
            (
                await session.scalars(
                    select(ReputationEvent).where(
                        ReputationEvent.evidence_id == appeal.decision_id,
                        ReputationEvent.reversed_at.is_(None),
                    )
                )
            ).all()
        )
        for event in events:
            event.reversed_at = datetime.now(UTC)
    correlation_id = request.state.correlation_id
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="appeal.resolved",
            resource_type="appeal",
            resource_id=appeal.id,
            correlation_id=correlation_id,
            payload={"decision": body.decision, "reason": body.reason},
        )
    )
    session.add(
        OutboxEvent(
            event_type="AppealResolved",
            aggregate_type="appeal",
            aggregate_id=appeal.id,
            payload={"appeal_id": str(appeal.id), "decision": body.decision},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=appeal.appellant_id,
            category="appeals",
            title="Appeal resolved",
            body=(
                "Your appeal was resolved with decision: "
                f"{body.decision.replace('_', ' ').lower()}."
            ),
            resource_path="/appeals",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    return {"id": appeal.id, "state": appeal.state}


@router.post("/ops/reputation-events", status_code=201)
async def create_reputation_event(
    body: ReputationEventCreate,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> dict[str, object]:
    event = ReputationEvent(
        student_user_id=body.student_user_id,
        project_id=body.project_id,
        dimension=body.dimension,
        value=body.value,
        evidence_type=body.evidence_type,
        evidence_id=body.evidence_id,
        approved_by_id=principal.user_id,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return {"id": event.id, "dimension": event.dimension, "value": event.value}


@router.get("/students/me/reputation-events")
async def my_reputation_events(principal: Principal, session: DbSession) -> list[dict[str, object]]:
    if principal.role != Role.STUDENT.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Student role required")
    rows = list(
        (
            await session.scalars(
                select(ReputationEvent)
                .where(ReputationEvent.student_user_id == principal.user_id)
                .order_by(ReputationEvent.created_at.desc())
            )
        ).all()
    )
    return [
        {
            "id": item.id,
            "dimension": item.dimension,
            "value": item.value,
            "evidence_type": item.evidence_type,
            "reversed_at": item.reversed_at,
        }
        for item in rows
    ]
