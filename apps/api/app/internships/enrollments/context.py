import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import CohortEnrollment, CohortTrack


@dataclass(frozen=True)
class EnrollmentContext:
    enrollment_id: uuid.UUID
    student_user_id: uuid.UUID
    cohort_id: uuid.UUID
    cohort_track_id: uuid.UUID
    track_version_id: uuid.UUID


async def resolve_enrollment_context(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    enrollment_id: uuid.UUID | None = None,
) -> EnrollmentContext:
    query = select(CohortEnrollment).where(
        CohortEnrollment.student_user_id == principal.user_id,
        CohortEnrollment.status.not_in(["WITHDRAWN", "TERMINATED"]),
    )
    if enrollment_id is not None:
        query = query.where(CohortEnrollment.id == enrollment_id)
        enrollment = await session.scalar(query)
    else:
        rows = list((await session.execute(query.order_by(CohortEnrollment.created_at))).scalars())
        if len(rows) > 1:
            raise ValueError("An explicit enrollment selection is required")
        enrollment = rows[0] if rows else None
    if enrollment is None:
        raise LookupError("Internship enrollment not found")
    cohort_track = await session.scalar(
        select(CohortTrack).where(
            CohortTrack.cohort_id == enrollment.cohort_id,
            CohortTrack.track_version_id == enrollment.track_version_id,
        )
    )
    if cohort_track is None:
        raise LookupError("Enrollment track is not configured for the cohort")
    return EnrollmentContext(
        enrollment_id=enrollment.id,
        student_user_id=enrollment.student_user_id,
        cohort_id=enrollment.cohort_id,
        cohort_track_id=cohort_track.id,
        track_version_id=enrollment.track_version_id,
    )
