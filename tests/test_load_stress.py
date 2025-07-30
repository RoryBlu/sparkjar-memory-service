import asyncio
import pytest
from httpx import AsyncClient
import external_api


@pytest.mark.asyncio
async def test_health_endpoint_load():
    async with AsyncClient(app=external_api.external_app, base_url="http://test") as client:
        tasks = [client.get("/health") for _ in range(20)]
        responses = await asyncio.gather(*tasks)
    assert len(responses) == 20
    assert all(r.status_code == 200 for r in responses)

