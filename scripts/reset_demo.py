import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from sqlalchemy import delete

from app.config import get_settings
from app.db import SessionFactory
from app.domain.models import Base


async def reset() -> None:
    settings = get_settings()
    if not settings.is_local_or_test:
        raise RuntimeError("Demo reset is refused outside local/test")
    async with SessionFactory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
    print("Removed local/test records. Run seed_demo.py to recreate Demo data.")


if __name__ == "__main__":
    asyncio.run(reset())
