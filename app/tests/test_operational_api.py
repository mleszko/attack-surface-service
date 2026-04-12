import os
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from attack_surface import app

TESTS_DIR = Path(__file__).resolve().parent


@pytest.mark.asyncio
async def test_healthz_readyz_and_request_id_propagation() -> None:
    os.environ["ENV_PATH"] = str(TESTS_DIR / "cloud.json")
    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            health = await client.get("/healthz")
            assert health.status_code == 200
            assert health.json() == {"status": "ok"}
            assert "X-Request-ID" in health.headers

            ready = await client.get("/readyz", headers={"X-Request-ID": "portfolio-test-id"})
            assert ready.status_code == 200
            assert ready.headers["X-Request-ID"] == "portfolio-test-id"
            payload = ready.json()
            assert payload["status"] == "ready"
            assert payload["vm_count"] > 0
            assert payload["workers"] > 0


@pytest.mark.asyncio
async def test_attack_not_found_returns_standard_error_contract() -> None:
    os.environ["ENV_PATH"] = str(TESTS_DIR / "cloud.json")
    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/attack?vm_id=vm-does-not-exist")
            assert response.status_code == 404
            payload = response.json()
            assert payload["error"]["code"] == "vm_not_found"
            assert payload["error"]["message"] == "VM not found"
            assert payload["error"]["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_validation_error_returns_standard_error_contract() -> None:
    os.environ["ENV_PATH"] = str(TESTS_DIR / "cloud.json")
    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/attack")
            assert response.status_code == 422
            payload = response.json()
            assert payload["error"]["code"] == "invalid_request"
            assert payload["error"]["message"] == "Request validation failed"
            assert isinstance(payload["error"]["details"], list)
