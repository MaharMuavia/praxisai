import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import RateLimitBucket


class RateLimitExceeded(ValueError):
    pass


async def consume_rate_limit(
    session: AsyncSession,
    *,
    raw_key: str,
    limit: int,
    window_seconds: int,
    commit: bool = True,
) -> None:
    bucket_key = hashlib.sha256(raw_key.encode()).hexdigest()
    now = datetime.now(UTC)
    for attempt in range(2):
        bucket = await session.scalar(
            select(RateLimitBucket)
            .where(RateLimitBucket.bucket_key == bucket_key)
            .with_for_update()
        )
        if bucket is None:
            session.add(
                RateLimitBucket(
                    bucket_key=bucket_key,
                    window_started_at=now,
                    request_count=1,
                )
            )
            try:
                if commit:
                    await session.commit()
                else:
                    await session.flush()
                return
            except IntegrityError:
                await session.rollback()
                if attempt == 0:
                    continue
                raise
        window_started_at = bucket.window_started_at
        if window_started_at.tzinfo is None:
            window_started_at = window_started_at.replace(tzinfo=UTC)
        if window_started_at + timedelta(seconds=window_seconds) <= now:
            bucket.window_started_at = now
            bucket.request_count = 1
        elif bucket.request_count >= limit:
            raise RateLimitExceeded("Rate limit exceeded; retry after the current window")
        else:
            bucket.request_count += 1
        if commit:
            await session.commit()
        return
