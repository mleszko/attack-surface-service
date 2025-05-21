import asyncio
import os
import time
import pytest
from httpx import AsyncClient, ASGITransport
from attack_surface import app

@pytest.mark.asyncio
async def test_attack_endpoint_under_load() -> None:
    """Simulate 1000 concurrent attack requests using default cloud.json."""
    vm_id = "vm-a"
    request_count = 1000
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def make_request():
            response = await client.get(f"/api/v1/attack?vm_id={vm_id}")
            assert response.status_code in (200, 429)

        tasks = [make_request() for _ in range(request_count)]
        await asyncio.gather(*tasks)

        stats_response = await client.get("/api/v1/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["request_count"] >= request_count

@pytest.mark.asyncio
async def test_attack_performance_with_large_env(monkeypatch) -> None:
    """Test single attack query performance with large input JSON."""
    os.environ["ENV_PATH"] = "tests/resources/huge_env.json"

    import importlib
    import attack_surface
    importlib.reload(attack_surface)

    vm_id = "vm-9999"
    transport = ASGITransport(app=attack_surface.app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.perf_counter()
        response = await client.get(f"/api/v1/attack?vm_id={vm_id}")
        duration = time.perf_counter() - start

        assert response.status_code in (200, 429)
        print(f"⏱️ Query duration with large env: {duration:.4f}s")
        assert duration < 1.0
