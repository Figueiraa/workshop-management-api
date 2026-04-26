import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_service_type(auth_client: AsyncClient):
    r = await auth_client.post("/service-types", json={
        "name": "Troca de óleo", "price": 120.0, "estimated_duration_minutes": 30
    })
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Troca de óleo"
    assert body["price"] == 120.0


@pytest.mark.asyncio
async def test_duplicate_name_returns_409(auth_client: AsyncClient):
    payload = {"name": "Alinhamento", "price": 80.0, "estimated_duration_minutes": 45}
    await auth_client.post("/service-types", json=payload)
    r = await auth_client.post("/service-types", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_service_types(auth_client: AsyncClient):
    await auth_client.post("/service-types", json={"name": "Balanceamento", "price": 60.0})
    r = await auth_client.get("/service-types")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_get_service_type_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.get("/service-types/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_service_type(auth_client: AsyncClient):
    r = await auth_client.post("/service-types", json={"name": "Revisão", "price": 200.0})
    sid = r.json()["id"]
    r = await auth_client.patch(f"/service-types/{sid}", json={"price": 250.0})
    assert r.status_code == 200
    assert r.json()["price"] == 250.0


@pytest.mark.asyncio
async def test_update_service_type_name_conflict_returns_409(auth_client: AsyncClient):
    await auth_client.post("/service-types", json={"name": "Serviço A", "price": 100.0})
    r = await auth_client.post("/service-types", json={"name": "Serviço B", "price": 200.0})
    sid = r.json()["id"]
    r = await auth_client.patch(f"/service-types/{sid}", json={"name": "Serviço A"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_service_type_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.patch("/service-types/9999", json={"price": 100.0})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_service_type(auth_client: AsyncClient):
    r = await auth_client.post("/service-types", json={"name": "Pintura", "price": 500.0})
    sid = r.json()["id"]
    r = await auth_client.delete(f"/service-types/{sid}")
    assert r.status_code == 204
    r = await auth_client.get(f"/service-types/{sid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_service_type_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.delete("/service-types/9999")
    assert r.status_code == 404
