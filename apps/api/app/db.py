from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings


def engine_options(settings: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {"pool_pre_ping": True}
    if settings.database_pool_mode == "transaction":
        options.update(
            poolclass=NullPool,
            connect_args={
                "prepared_statement_cache_size": 0,
                "statement_cache_size": 0,
            },
        )
    return options


settings = get_settings()
engine = create_async_engine(settings.database_url, **engine_options(settings))
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
