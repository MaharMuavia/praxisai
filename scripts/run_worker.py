import argparse
import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.db import SessionFactory
from app.domain.models import OutboxEvent
from app.intake.service import anonymize_expired_submissions
from app.notifications.service import process_pending_notifications
from app.outbox.service import process_one
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def process_retention_sweep(session: AsyncSession) -> tuple[int, int]:
    pending = await session.scalar(
        select(OutboxEvent)
        .where(
            OutboxEvent.event_type == "RetentionSweepRequested",
            OutboxEvent.status == "PENDING",
        )
        .order_by(OutboxEvent.created_at)
    )
    if pending is None:
        pending = OutboxEvent(
            event_type="RetentionSweepRequested",
            aggregate_type="public_intake",
            aggregate_id=uuid.uuid4(),
            payload={"requested_at": datetime.now(UTC).isoformat()},
        )
        session.add(pending)
        await session.commit()

    async def handler(_: dict[str, object]) -> None:
        await anonymize_expired_submissions(session, now=datetime.now(UTC))

    try:
        await process_one(
            session,
            handlers={"RetentionSweepRequested": handler},
            event_id=pending.id,
        )
        return 1, 0
    except Exception:
        return 0, 1


async def run(*, limit: int) -> int:
    async with SessionFactory() as session:
        succeeded, failed = await process_pending_notifications(session, limit=limit)
        retention_succeeded, retention_failed = await process_retention_sweep(session)
    print(
        f"Notification jobs: {succeeded} succeeded, {failed} failed; "
        f"retention jobs: {retention_succeeded} succeeded, {retention_failed} failed"
    )
    return 1 if failed or retention_failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process pending PraxisAI outbox jobs once."
    )
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.limit <= 1_000:
        parser.error("--limit must be between 1 and 1000")
    return asyncio.run(run(limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
