import asyncio
import pytest
from httpx import AsyncClient
from attack_surface import app

@pytest.mark.asyncio
async def test_attack_endpoint_under_load():
    vm_id = "vm-a"
    request_count = 1000

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        async def make_request():
            response = await client.get(f"/api/v1/attack?vm_id={vm_id}")
            assert response.status_code in (200, 429)

        tasks = [make_request() for _ in range(request_count)]
        await asyncio.gather(*tasks)

        stats_response = await client.get("/api/v1/stats")
        assert stats_response.status_code == 200
