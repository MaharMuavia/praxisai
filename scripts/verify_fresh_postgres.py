"""Run the complete Alembic graph in an isolated PostgreSQL schema."""

import asyncio
import os
import sys
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))


async def verify_fresh_upgrade() -> None:
    database_url = os.environ.get("DATABASE_MIGRATION_URL") or os.environ.get(
        "DATABASE_URL"
    )
    if database_url and database_url.startswith("postgresql://"):
        database_url = "postgresql+asyncpg://" + database_url.removeprefix(
            "postgresql://"
        )
    elif database_url and database_url.startswith("postgres://"):
        database_url = "postgresql+asyncpg://" + database_url.removeprefix(
            "postgres://"
        )
    if not database_url or not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "DATABASE_MIGRATION_URL or DATABASE_URL must be a PostgreSQL async URL"
        )
    schema = f"migration_probe_{uuid.uuid4().hex}"
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.execute(text(f'SET search_path TO "{schema}"'))
            try:

                def upgrade(sync_connection) -> None:
                    config = Config(str(API_ROOT / "alembic.ini"))
                    config.attributes["connection"] = sync_connection
                    command.upgrade(config, "head")

                await connection.run_sync(upgrade)
                version = await connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
                if version != "c3d4e5f6a7b8":
                    raise RuntimeError(
                        f"Fresh PostgreSQL schema stopped at unexpected revision: {version}"
                    )
            finally:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    finally:
        await engine.dispose()
    print(
        f"Fresh PostgreSQL migration probe reached head c3d4e5f6a7b8 in schema {schema}"
    )


if __name__ == "__main__":
    asyncio.run(verify_fresh_upgrade())
