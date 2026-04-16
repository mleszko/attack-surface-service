import pytest
from httpx import ASGITransport, AsyncClient

from attack_surface import app


@pytest.mark.asyncio
async def test_openapi_includes_attack_error_examples() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

    attack_get = schema["paths"]["/api/v1/attack"]["get"]
    responses = attack_get["responses"]

    assert responses["404"]["content"]["application/json"]["example"]["error"]["code"] == "vm_not_found"
    assert responses["422"]["content"]["application/json"]["example"]["error"]["code"] == "invalid_request"
    assert responses["429"]["content"]["application/json"]["example"]["error"]["code"] == "too_busy"
    assert responses["503"]["content"]["application/json"]["example"]["error"]["code"] == "processing_timeout"


@pytest.mark.asyncio
async def test_openapi_includes_probe_examples() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

    health_get = schema["paths"]["/healthz"]["get"]
    ready_get = schema["paths"]["/readyz"]["get"]

    assert health_get["responses"]["200"]["content"]["application/json"]["example"]["status"] == "ok"
    assert ready_get["responses"]["200"]["content"]["application/json"]["example"]["status"] == "ready"
    assert (
        ready_get["responses"]["503"]["content"]["application/json"]["example"]["error"]["code"]
        == "service_not_ready"
    )
