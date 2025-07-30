import asyncio
import pytest
from httpx import AsyncClient
import external_api


@pytest.mark.asyncio
async def test_concurrent_health_requests():
    async with AsyncClient(app=external_api.external_app, base_url="http://test") as client:
        tasks = [client.get("/health") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in responses)

