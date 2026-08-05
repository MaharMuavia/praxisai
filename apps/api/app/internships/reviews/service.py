import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    CohortTrack,
    InternshipCohortAssignment,
    InternshipReview,
    InternshipStudentAssignment,
    OrganizationMembership,
    User,
)


class ReviewAssignmentError(ValueError):
    """The proposed reviewer is not eligible for the review."""


async def assign_reviewer(
    session: AsyncSession,
    *,
    review: InternshipReview,
    reviewer_id: uuid.UUID,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> None:
    assignment = await session.get(InternshipStudentAssignment, review.student_assignment_id)
    reviewer = await session.get(User, reviewer_id)
    if assignment is None or reviewer is None or not reviewer.is_active:
        raise ReviewAssignmentError("Reviewer or student assignment does not exist")
    if assignment.student_user_id == reviewer_id:
        raise ReviewAssignmentError("A student cannot review their own assignment")
    roles = (
        await session.execute(
            select(OrganizationMembership.role).where(
                OrganizationMembership.user_id == reviewer_id,
                OrganizationMembership.is_active.is_(True),
                OrganizationMembership.role.in_(["reviewer", "technical_lead"]),
            )
        )
    ).scalars().all()
    if not roles:
        raise ReviewAssignmentError("Reviewer does not have a review capability")
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id
    )
    if cohort_assignment is None:
        raise ReviewAssignmentError("Cohort assignment does not exist")
    cohort_track = await session.get(CohortTrack, cohort_assignment.cohort_track_id)
    if cohort_track is None:
        raise ReviewAssignmentError("Cohort track does not exist")
    pool = {str(value) for value in cohort_assignment.reviewer_pool}
    pool.update(str(value) for value in cohort_track.reviewer_pool)
    if str(reviewer_id) != str(cohort_track.instructor_id) and str(reviewer_id) not in pool:
        raise ReviewAssignmentError("Reviewer is not assigned to this cohort or reviewer pool")
    review.reviewer_id = reviewer_id
    review.status = "ASSIGNED"
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="internship.review_assigned",
            resource_type="internship_review",
            resource_id=review.id,
            correlation_id=correlation_id,
            payload={"reviewer_id": str(reviewer_id)},
        )
    )
