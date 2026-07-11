import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_checks_database(client: AsyncClient):
    r = await client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "database": "connected"}


@pytest.mark.asyncio
async def test_request_id_header_is_returned(client: AsyncClient):
    r = await client.get("/health")
    assert r.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_request_id_is_propagated(client: AsyncClient):
    r = await client.get("/health", headers={"X-Request-ID": "trace-123"})
    assert r.headers.get("X-Request-ID") == "trace-123"


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    r = await client.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Content-Security-Policy") == "default-src 'self'"


@pytest.mark.asyncio
async def test_api_is_versioned(client: AsyncClient):
    # Sem o prefixo de versão, a rota não existe.
    assert (await client.get("/clients")).status_code == 404
    # Com o prefixo, exige autenticação (401), provando que a rota vive sob /api/v1.
    assert (await client.get("/api/v1/clients")).status_code == 401
