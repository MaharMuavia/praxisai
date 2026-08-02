import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.models import Base
from app.rate_limits.service import RateLimitExceeded, consume_rate_limit


@pytest.mark.asyncio
async def test_database_rate_limit_is_shared_across_sessions() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as first:
        await consume_rate_limit(first, raw_key="auth:127.0.0.1", limit=2, window_seconds=60)
    async with factory() as second:
        await consume_rate_limit(second, raw_key="auth:127.0.0.1", limit=2, window_seconds=60)
    async with factory() as third:
        with pytest.raises(RateLimitExceeded):
            await consume_rate_limit(
                third,
                raw_key="auth:127.0.0.1",
                limit=2,
                window_seconds=60,
            )

    await engine.dispose()
