import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_client(auth_client: AsyncClient):
    r = await auth_client.post(
        "/clients",
        json={
            "name": "João Silva",
            "cpf_cnpj": "529.982.247-25",
            "phone": "11999999999",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["cpf_cnpj"] == "52998224725"
    assert body["name"] == "João Silva"


@pytest.mark.asyncio
async def test_duplicate_cpf_returns_409(auth_client: AsyncClient):
    payload = {"name": "A", "cpf_cnpj": "529.982.247-25"}
    await auth_client.post("/clients", json=payload)
    r = await auth_client.post("/clients", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_clients(auth_client: AsyncClient):
    await auth_client.post("/clients", json={"name": "A", "cpf_cnpj": "529.982.247-25"})
    r = await auth_client.get("/clients")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_update_client(auth_client: AsyncClient):
    r = await auth_client.post("/clients", json={"name": "A", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    r = await auth_client.patch(f"/clients/{cid}", json={"name": "B"})
    assert r.status_code == 200
    assert r.json()["name"] == "B"


@pytest.mark.asyncio
async def test_delete_client(auth_client: AsyncClient):
    r = await auth_client.post("/clients", json={"name": "A", "cpf_cnpj": "529.982.247-25"})
    cid = r.json()["id"]
    r = await auth_client.delete(f"/clients/{cid}")
    assert r.status_code == 204
    r = await auth_client.get(f"/clients/{cid}")
    assert r.status_code == 404
