from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from alembic.config import Config
from alembic.script import ScriptDirectory


class DatabaseSchemaNotReady(RuntimeError):
    """Raised when the connected database is not at the application migration head."""


def repository_migration_heads() -> frozenset[str]:
    api_root = Path(__file__).resolve().parents[1]
    config = Config(str(api_root / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    return frozenset(script.get_heads())


EXPECTED_DATABASE_REVISIONS = repository_migration_heads()


async def assert_database_ready(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        await session.execute(text("SELECT 1"))
        result = await session.execute(text("SELECT version_num FROM alembic_version"))
        current_revisions = frozenset(result.scalars().all())

    if current_revisions != EXPECTED_DATABASE_REVISIONS:
        raise DatabaseSchemaNotReady("Database migration revision does not match the application")
