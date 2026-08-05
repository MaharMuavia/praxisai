import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import InternshipTrackVersion


async def published_track_version(
    session: AsyncSession, *, track_version_id: uuid.UUID
) -> InternshipTrackVersion | None:
    result = await session.scalar(
        select(InternshipTrackVersion).where(
            InternshipTrackVersion.id == track_version_id,
            InternshipTrackVersion.status == "PUBLISHED",
        )
    )
    return result
