import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.db import SessionFactory
from app.notifications.service import process_pending_notifications


async def run(*, limit: int) -> int:
    async with SessionFactory() as session:
        succeeded, failed = await process_pending_notifications(session, limit=limit)
    print(f"Notification jobs: {succeeded} succeeded, {failed} failed")
    return 1 if failed else 0


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
