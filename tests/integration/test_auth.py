import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={"username": "user1", "email": "u@test.com", "password": "pass"})
    assert r.status_code == 201
    assert r.json()["username"] == "user1"

    r = await client.post("/api/v1/auth/login", data={"username": "user1", "password": "pass"})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"username": "user1", "email": "u@test.com", "password": "pass"})
    r = await client.post("/api/v1/auth/login", data={"username": "user1", "password": "pass"})
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "user1"


@pytest.mark.asyncio
async def test_duplicate_username_returns_409(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"username": "user1", "email": "a@test.com", "password": "p"})
    r = await client.post("/api/v1/auth/register", json={"username": "user1", "email": "b@test.com", "password": "p"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_duplicate_email_returns_409(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"username": "user1", "email": "same@test.com", "password": "p"})
    r = await client.post("/api/v1/auth/register", json={"username": "user2", "email": "same@test.com", "password": "p"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", data={"username": "ghost", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    client.headers.update({"Authorization": "Bearer token.invalido.aqui"})
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
