import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import InternshipApplication


async def active_application_for_cohort(
    session: AsyncSession, *, student_user_id: uuid.UUID, cohort_id: uuid.UUID, statuses: set[str]
) -> InternshipApplication | None:
    result = await session.scalar(
        select(InternshipApplication)
        .where(
            InternshipApplication.applicant_user_id == student_user_id,
            InternshipApplication.cohort_id == cohort_id,
            InternshipApplication.status.in_(statuses),
        )
        .with_for_update()
    )
    return result
