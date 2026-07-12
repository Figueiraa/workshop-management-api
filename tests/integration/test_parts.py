import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_part(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={
        "name": "Filtro de óleo", "unit_price": 35.0, "stock_quantity": 20, "unit": "un"
    })
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Filtro de óleo"
    assert body["stock_quantity"] == 20


@pytest.mark.asyncio
async def test_list_parts(auth_client: AsyncClient):
    await auth_client.post("/api/v1/parts", json={"name": "Vela", "unit_price": 15.0, "stock_quantity": 50})
    r = await auth_client.get("/api/v1/parts")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_get_part_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/parts/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_part(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={"name": "Correia", "unit_price": 80.0, "stock_quantity": 10})
    pid = r.json()["id"]
    r = await auth_client.patch(f"/api/v1/parts/{pid}", json={"unit_price": 95.0})
    assert r.status_code == 200
    assert r.json()["unit_price"] == 95.0


@pytest.mark.asyncio
async def test_update_part_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.patch("/api/v1/parts/9999", json={"unit_price": 10.0})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stock_adjust_add(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={"name": "Óleo", "unit_price": 40.0, "stock_quantity": 5})
    pid = r.json()["id"]
    r = await auth_client.post(f"/api/v1/parts/{pid}/stock", json={"quantity": 10})
    assert r.status_code == 200
    assert r.json()["stock_quantity"] == 15


@pytest.mark.asyncio
async def test_stock_adjust_remove(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={"name": "Óleo", "unit_price": 40.0, "stock_quantity": 10})
    pid = r.json()["id"]
    r = await auth_client.post(f"/api/v1/parts/{pid}/stock", json={"quantity": -3})
    assert r.status_code == 200
    assert r.json()["stock_quantity"] == 7


@pytest.mark.asyncio
async def test_stock_adjust_below_zero_returns_422(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={"name": "Óleo", "unit_price": 40.0, "stock_quantity": 2})
    pid = r.json()["id"]
    r = await auth_client.post(f"/api/v1/parts/{pid}/stock", json={"quantity": -10})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_stock_adjust_part_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts/9999/stock", json={"quantity": 5})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_part(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/parts", json={"name": "Parafuso", "unit_price": 2.0, "stock_quantity": 100})
    pid = r.json()["id"]
    r = await auth_client.delete(f"/api/v1/parts/{pid}")
    assert r.status_code == 204
    r = await auth_client.get(f"/api/v1/parts/{pid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_part_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.delete("/api/v1/parts/9999")
    assert r.status_code == 404
