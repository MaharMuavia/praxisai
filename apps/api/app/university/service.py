import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.config import Settings
from app.domain.enums import ProjectState
from app.domain.models import (
    AuditEvent,
    Credential,
    ExportJob,
    InstitutionalAgreement,
    Organization,
    OutboxEvent,
    Project,
    ProjectAssignment,
    StudentProfile,
    University,
    UniversityEnrollment,
    WorkLog,
)
from app.domain.schemas import UniversityMetrics


class UniversityAccessError(ValueError):
    pass


class UniversityConflict(UniversityAccessError):
    pass


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def _authorized_university(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    entitlement: str,
) -> University:
    university = await session.scalar(
        select(University).where(University.organization_id == principal.organization_id)
    )
    if university is None or university.agreement_status != "ACTIVE":
        raise UniversityAccessError("The university has no active institutional agreement")
    now = datetime.now(UTC)
    agreements = list(
        (
            await session.scalars(
                select(InstitutionalAgreement)
                .where(
                    InstitutionalAgreement.university_id == university.id,
                    InstitutionalAgreement.status == "ACTIVE",
                )
                .order_by(InstitutionalAgreement.version.desc())
            )
        ).all()
    )
    agreement = next(
        (
            item
            for item in agreements
            if _utc(item.starts_at) <= now and (item.ends_at is None or _utc(item.ends_at) > now)
        ),
        None,
    )
    if agreement is None or entitlement not in agreement.entitlements:
        raise UniversityAccessError(f"Agreement does not grant {entitlement}")
    return university


async def aggregate_metrics(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    settings: Settings,
) -> UniversityMetrics:
    university = await _authorized_university(
        session, principal=principal, entitlement="aggregate_metrics"
    )
    profile_ids = list(
        (
            await session.scalars(
                select(UniversityEnrollment.student_profile_id).where(
                    UniversityEnrollment.university_id == university.id,
                    UniversityEnrollment.consented.is_(True),
                )
            )
        ).all()
    )
    minimum = settings.university_minimum_cohort_size
    now = datetime.now(UTC)
    if len(profile_ids) < minimum:
        return UniversityMetrics(
            suppressed=True,
            minimum_cohort_size=minimum,
            consented_cohort_size=None,
            participating_students=None,
            completed_projects=None,
            credentials_issued=None,
            verified_work_minutes=None,
            as_of=now,
        )

    user_ids = list(
        (
            await session.scalars(
                select(StudentProfile.user_id).where(StudentProfile.id.in_(profile_ids))
            )
        ).all()
    )
    organization = await session.get(Organization, principal.organization_id)
    include_demo = bool(organization and organization.is_demo)
    project_filter = true() if include_demo else Project.is_demo.is_(False)
    participating = await session.scalar(
        select(func.count(distinct(ProjectAssignment.user_id)))
        .join(Project, Project.id == ProjectAssignment.project_id)
        .where(ProjectAssignment.user_id.in_(user_ids), project_filter)
    )
    completed = await session.scalar(
        select(func.count(distinct(ProjectAssignment.project_id)))
        .join(Project, Project.id == ProjectAssignment.project_id)
        .where(
            ProjectAssignment.user_id.in_(user_ids),
            Project.state == ProjectState.COMPLETED.value,
            project_filter,
        )
    )
    credentials = await session.scalar(
        select(func.count(Credential.id))
        .join(Project, Project.id == Credential.project_id)
        .where(Credential.student_user_id.in_(user_ids), project_filter)
    )
    minutes = await session.scalar(
        select(func.coalesce(func.sum(WorkLog.minutes), 0))
        .join(Project, Project.id == WorkLog.project_id)
        .where(
            WorkLog.student_user_id.in_(user_ids),
            WorkLog.submitted_at.is_not(None),
            project_filter,
        )
    )
    return UniversityMetrics(
        suppressed=False,
        minimum_cohort_size=minimum,
        consented_cohort_size=len(profile_ids),
        participating_students=participating or 0,
        completed_projects=completed or 0,
        credentials_issued=credentials or 0,
        verified_work_minutes=minutes or 0,
        as_of=now,
    )


async def request_export(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    purpose: str,
    idempotency_key: str,
    correlation_id: uuid.UUID,
    settings: Settings,
) -> ExportJob:
    await _authorized_university(session, principal=principal, entitlement="exports")
    metrics = await aggregate_metrics(session, principal=principal, settings=settings)
    if metrics.suppressed:
        raise UniversityConflict(
            "Export is unavailable while the consented cohort is below the privacy threshold"
        )
    existing = await session.scalar(
        select(ExportJob).where(ExportJob.idempotency_key == idempotency_key)
    )
    if existing is not None:
        if existing.organization_id != principal.organization_id:
            raise UniversityConflict("Idempotency key belongs to a different organization")
        return existing

    export = ExportJob(
        organization_id=principal.organization_id,
        requested_by_id=principal.user_id,
        purpose=purpose,
        status="PENDING",
        storage_key=None,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        idempotency_key=idempotency_key,
    )
    session.add(export)
    await session.flush()
    session.add_all(
        [
            AuditEvent(
                actor_id=principal.user_id,
                organization_id=principal.organization_id,
                action="university.export_requested",
                resource_type="export_job",
                resource_id=export.id,
                correlation_id=correlation_id,
                payload={"purpose": purpose, "expires_at": export.expires_at.isoformat()},
            ),
            OutboxEvent(
                event_type="UniversityExportRequested",
                aggregate_type="export_job",
                aggregate_id=export.id,
                payload={
                    "export_job_id": str(export.id),
                    "organization_id": str(principal.organization_id),
                },
            ),
        ]
    )
    await session.commit()
    await session.refresh(export)
    return export


async def list_exports(session: AsyncSession, *, principal: SessionPrincipal) -> list[ExportJob]:
    await _authorized_university(session, principal=principal, entitlement="exports")
    return list(
        (
            await session.scalars(
                select(ExportJob)
                .where(ExportJob.organization_id == principal.organization_id)
                .order_by(ExportJob.created_at.desc())
            )
        ).all()
    )
