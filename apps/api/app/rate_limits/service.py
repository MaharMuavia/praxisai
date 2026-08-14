import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import RateLimitBucket


class RateLimitExceeded(ValueError):
    pass


def opaque_rate_limit_key(*, namespace: str, identifier: str) -> str:
    """Build a stable rate-limit key without retaining credentials or PII.

    The returned value is hashed again before persistence by ``consume_rate_limit``.
    Keeping the first hash here prevents callers, traces, or future diagnostics from
    accidentally exposing the identifier used to partition the limit.
    """
    normalized_namespace = namespace.strip(": ")
    if not normalized_namespace:
        raise ValueError("Rate-limit namespace is required")
    if not identifier:
        raise ValueError("Rate-limit identifier is required")
    fingerprint = hashlib.sha256(identifier.encode()).hexdigest()
    return f"{normalized_namespace}:sha256:{fingerprint}"


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
            new_bucket = RateLimitBucket(
                bucket_key=bucket_key,
                window_started_at=now,
                request_count=1,
            )
            try:
                if commit:
                    session.add(new_bucket)
                    await session.commit()
                else:
                    # Contain a concurrent first-insert conflict in a savepoint so
                    # callers do not lose their surrounding business transaction.
                    async with session.begin_nested():
                        session.add(new_bucket)
                        await session.flush()
                return
            except IntegrityError:
                if commit:
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
