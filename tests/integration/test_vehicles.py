import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_vehicle(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]

    r = await auth_client.post("/api/v1/vehicles", json={
        "plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid
    })
    assert r.status_code == 201
    body = r.json()
    assert body["plate"] == "ABC1234"
    assert body["client_id"] == cid


@pytest.mark.asyncio
async def test_create_vehicle_mercosul_plate(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "Maria", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    r = await auth_client.post("/api/v1/vehicles", json={
        "plate": "ABC1D23", "brand": "Fiat", "model": "Pulse", "year": 2023, "client_id": cid
    })
    assert r.status_code == 201
    assert r.json()["plate"] == "ABC1D23"


@pytest.mark.asyncio
async def test_duplicate_plate_returns_409(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    payload = {"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid}
    await auth_client.post("/api/v1/vehicles", json=payload)
    r = await auth_client.post("/api/v1/vehicles", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_vehicle_client_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/vehicles", json={
        "plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": 9999
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_vehicles(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    await auth_client.post("/api/v1/vehicles", json={"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid})
    r = await auth_client.get("/api/v1/vehicles")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_list_vehicles_by_client(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    await auth_client.post("/api/v1/vehicles", json={"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid})
    r = await auth_client.get(f"/api/v1/vehicles/client/{cid}")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_list_vehicles_by_invalid_client_returns_404(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/vehicles/client/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_vehicle_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/vehicles/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_vehicle(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    r = await auth_client.post("/api/v1/vehicles", json={"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid})
    vid = r.json()["id"]
    r = await auth_client.patch(f"/api/v1/vehicles/{vid}", json={"model": "Fox", "year": 2021})
    assert r.status_code == 200
    assert r.json()["model"] == "Fox"
    assert r.json()["year"] == 2021


@pytest.mark.asyncio
async def test_update_vehicle_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.patch("/api/v1/vehicles/9999", json={"model": "Fox"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_vehicle(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    r = await auth_client.post("/api/v1/vehicles", json={"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": cid})
    vid = r.json()["id"]
    r = await auth_client.delete(f"/api/v1/vehicles/{vid}")
    assert r.status_code == 204
    r = await auth_client.get(f"/api/v1/vehicles/{vid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_vehicle_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.delete("/api/v1/vehicles/9999")
    assert r.status_code == 404
