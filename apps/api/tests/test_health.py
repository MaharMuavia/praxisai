import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_is_available_at_root_and_api_prefix() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        root_response = await client.get("/health")
        api_response = await client.get("/api/v1/health")

    assert root_response.status_code == 200
    assert api_response.status_code == 200
    assert root_response.json() == {"status": "ok"}
    assert api_response.json() == {"status": "ok"}
