import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    LearningEnrollment,
    LearningModule,
    LearningModuleCompletion,
    LearningPath,
    StudentProfile,
)
from app.domain.schemas import (
    LearningContentSection,
    LearningModuleCompleteRequest,
    LearningModuleView,
    LearningPathView,
)


class LearningError(ValueError):
    pass


class LearningNotFound(LearningError):
    pass


async def _path_view(
    session: AsyncSession, *, path: LearningPath, student_user_id: uuid.UUID
) -> LearningPathView:
    modules = list(
        (
            await session.scalars(
                select(LearningModule)
                .where(LearningModule.learning_path_id == path.id)
                .order_by(LearningModule.ordinal)
            )
        ).all()
    )
    enrollment = await session.scalar(
        select(LearningEnrollment).where(
            LearningEnrollment.learning_path_id == path.id,
            LearningEnrollment.student_user_id == student_user_id,
        )
    )
    completed_ids: set[uuid.UUID] = set()
    if enrollment is not None:
        completed_ids = set(
            (
                await session.scalars(
                    select(LearningModuleCompletion.learning_module_id).where(
                        LearningModuleCompletion.enrollment_id == enrollment.id
                    )
                )
            ).all()
        )
    module_count = len(modules)
    progress = round(len(completed_ids) / module_count * 100) if module_count else 0
    return LearningPathView(
        id=path.id,
        slug=path.slug,
        title=path.title,
        summary=path.summary,
        level=path.level,
        estimated_hours=path.estimated_hours,
        skill_outcomes=path.skill_outcomes,
        prerequisites=path.prerequisites,
        modules=[
            LearningModuleView(
                id=module.id,
                ordinal=module.ordinal,
                title=module.title,
                summary=module.summary,
                estimated_minutes=module.estimated_minutes,
                content_sections=[
                    LearningContentSection.model_validate(section)
                    for section in module.content_sections
                ],
                exercise_brief=module.exercise_brief,
                completion_evidence=module.completion_evidence,
                completed=module.id in completed_ids,
            )
            for module in modules
        ],
        enrolled=enrollment is not None,
        progress_percent=progress,
        status=enrollment.status if enrollment else None,
    )


async def list_learning_paths(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[LearningPathView]:
    paths = list(
        (
            await session.scalars(
                select(LearningPath)
                .where(LearningPath.active.is_(True))
                .order_by(LearningPath.level, LearningPath.title)
            )
        ).all()
    )
    return [
        await _path_view(session, path=path, student_user_id=principal.user_id) for path in paths
    ]


async def enroll_in_path(
    session: AsyncSession,
    *,
    path_id: uuid.UUID,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> LearningPathView:
    profile = await session.scalar(
        select(StudentProfile).where(StudentProfile.user_id == principal.user_id)
    )
    if profile is None or not profile.eligible or not profile.confirmed_18_plus:
        raise LearningError("An eligible, age-confirmed student profile is required")
    path = await session.get(LearningPath, path_id)
    if path is None or not path.active:
        raise LearningNotFound("Learning path not found")
    enrollment = await session.scalar(
        select(LearningEnrollment).where(
            LearningEnrollment.learning_path_id == path.id,
            LearningEnrollment.student_user_id == principal.user_id,
        )
    )
    if enrollment is None:
        enrollment = LearningEnrollment(
            learning_path_id=path.id,
            student_user_id=principal.user_id,
            status="IN_PROGRESS",
            enrolled_at=datetime.now(UTC),
        )
        session.add(enrollment)
        session.add(
            AuditEvent(
                actor_id=principal.user_id,
                organization_id=principal.organization_id,
                action="learning.enrolled",
                resource_type="learning_path",
                resource_id=path.id,
                correlation_id=correlation_id,
                payload={"path_slug": path.slug},
            )
        )
        await session.commit()
    return await _path_view(session, path=path, student_user_id=principal.user_id)


async def complete_module(
    session: AsyncSession,
    *,
    module_id: uuid.UUID,
    body: LearningModuleCompleteRequest,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> LearningPathView:
    module = await session.get(LearningModule, module_id)
    if module is None:
        raise LearningNotFound("Learning module not found")
    path = await session.get(LearningPath, module.learning_path_id)
    if path is None or not path.active:
        raise LearningNotFound("Learning path not found")
    enrollment = await session.scalar(
        select(LearningEnrollment)
        .where(
            LearningEnrollment.learning_path_id == path.id,
            LearningEnrollment.student_user_id == principal.user_id,
        )
        .with_for_update()
    )
    if enrollment is None:
        raise LearningError("Enroll in this learning path before completing modules")
    if module.ordinal > 1:
        previous_module = await session.scalar(
            select(LearningModule).where(
                LearningModule.learning_path_id == path.id,
                LearningModule.ordinal == module.ordinal - 1,
            )
        )
        previous_complete = (
            await session.scalar(
                select(LearningModuleCompletion.id).where(
                    LearningModuleCompletion.enrollment_id == enrollment.id,
                    LearningModuleCompletion.learning_module_id == previous_module.id,
                )
            )
            if previous_module is not None
            else None
        )
        if previous_complete is None:
            raise LearningError("Complete the previous module first")
    completion = await session.scalar(
        select(LearningModuleCompletion).where(
            LearningModuleCompletion.enrollment_id == enrollment.id,
            LearningModuleCompletion.learning_module_id == module.id,
        )
    )
    if completion is None:
        completion = LearningModuleCompletion(
            enrollment_id=enrollment.id,
            learning_module_id=module.id,
            evidence_summary=body.evidence_summary,
            completed_at=datetime.now(UTC),
        )
        session.add(completion)
        session.add(
            AuditEvent(
                actor_id=principal.user_id,
                organization_id=principal.organization_id,
                action="learning.module_completed",
                resource_type="learning_module",
                resource_id=module.id,
                correlation_id=correlation_id,
                payload={"evidence_summary": body.evidence_summary},
            )
        )
        await session.flush()
    module_count = int(
        await session.scalar(
            select(func.count(LearningModule.id)).where(LearningModule.learning_path_id == path.id)
        )
        or 0
    )
    completion_count = int(
        await session.scalar(
            select(func.count(LearningModuleCompletion.id)).where(
                LearningModuleCompletion.enrollment_id == enrollment.id
            )
        )
        or 0
    )
    if module_count and completion_count == module_count:
        enrollment.status = "COMPLETED"
        enrollment.completed_at = datetime.now(UTC)
    await session.commit()
    return await _path_view(session, path=path, student_user_id=principal.user_id)
