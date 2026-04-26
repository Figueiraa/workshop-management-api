import pytest
from httpx import AsyncClient


async def _create_client(c: AsyncClient) -> int:
    r = await c.post("/clients", json={"name": "João", "cpf_cnpj": "529.982.247-25"})
    return r.json()["id"]


async def _create_vehicle(c: AsyncClient, client_id: int) -> int:
    r = await c.post(
        "/vehicles", json={"plate": "ABC1234", "brand": "VW", "model": "Gol", "year": 2020, "client_id": client_id}
    )
    return r.json()["id"]


async def _create_service_type(c: AsyncClient) -> int:
    r = await c.post("/service-types", json={"name": "Troca de óleo", "price": 150.0, "estimated_duration_minutes": 30})
    return r.json()["id"]


async def _create_part(c: AsyncClient) -> int:
    r = await c.post("/parts", json={"name": "Óleo 5W30", "unit_price": 45.0, "stock_quantity": 10, "unit": "L"})
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_service_order(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    sid = await _create_service_type(auth_client)
    pid = await _create_part(auth_client)

    r = await auth_client.post("/service-orders", json={
        "vehicle_id": vid,
        "notes": "Cliente relata barulho no motor",
        "items": [{"service_type_id": sid, "quantity": 1}],
        "parts": [{"part_id": pid, "quantity": 2}],
    })
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "RECEBIDA"
    assert body["client_id"] == cid
    assert body["total_budget"] == 150.0 + 45.0 * 2  # 240.0


@pytest.mark.asyncio
async def test_create_service_order_vehicle_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.post("/service-orders", json={"vehicle_id": 9999})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_service_order_service_type_not_found_returns_404(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={
        "vehicle_id": vid,
        "items": [{"service_type_id": 9999, "quantity": 1}],
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_service_order_part_not_found_returns_404(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={
        "vehicle_id": vid,
        "parts": [{"part_id": 9999, "quantity": 1}],
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_all_service_orders(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    await auth_client.post("/service-orders", json={"vehicle_id": vid})
    r = await auth_client.get("/service-orders")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_list_service_orders_by_status(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    await auth_client.post("/service-orders", json={"vehicle_id": vid})
    r = await auth_client.get("/service-orders?status=RECEBIDA")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await auth_client.get("/service-orders?status=ENTREGUE")
    assert r.status_code == 200
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_get_service_order_by_id(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]

    r = await auth_client.get(f"/service-orders/{oid}")
    assert r.status_code == 200
    assert r.json()["id"] == oid


@pytest.mark.asyncio
async def test_get_service_order_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.get("/service-orders/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_status_transition_flow(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]

    for next_status in ["EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO", "EM_EXECUCAO", "FINALIZADA", "ENTREGUE"]:
        r = await auth_client.patch(f"/service-orders/{oid}/status", json={"status": next_status})
        assert r.status_code == 200
        assert r.json()["status"] == next_status


@pytest.mark.asyncio
async def test_update_status_timestamps(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]

    await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "EM_DIAGNOSTICO"})
    await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "AGUARDANDO_APROVACAO"})
    r = await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "EM_EXECUCAO"})
    assert r.json()["started_at"] is not None

    r = await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "FINALIZADA"})
    assert r.json()["completed_at"] is not None

    r = await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "ENTREGUE"})
    assert r.json()["delivered_at"] is not None


@pytest.mark.asyncio
async def test_invalid_status_transition_returns_422(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]
    r = await auth_client.patch(f"/service-orders/{oid}/status", json={"status": "ENTREGUE"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_status_order_not_found_returns_404(auth_client: AsyncClient):
    r = await auth_client.patch("/service-orders/9999/status", json={"status": "EM_DIAGNOSTICO"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_insufficient_stock_returns_422(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    pid = await _create_part(auth_client)
    r = await auth_client.post("/service-orders", json={
        "vehicle_id": vid,
        "parts": [{"part_id": pid, "quantity": 999}],
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_average_execution_time_no_data(auth_client: AsyncClient):
    r = await auth_client.get("/service-orders/metrics/average-execution-time")
    assert r.status_code == 200
    body = r.json()
    assert body["total_completed"] == 0
    assert body["average_minutes"] is None


@pytest.mark.asyncio
async def test_average_execution_time_with_completed_order(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]

    for s in ["EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO", "EM_EXECUCAO", "FINALIZADA", "ENTREGUE"]:
        await auth_client.patch(f"/service-orders/{oid}/status", json={"status": s})

    r = await auth_client.get("/service-orders/metrics/average-execution-time")
    assert r.status_code == 200
    assert r.json()["total_completed"] == 1
    assert r.json()["average_minutes"] is not None


@pytest.mark.asyncio
async def test_public_status_endpoint(auth_client: AsyncClient, client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    r = await auth_client.post("/service-orders", json={"vehicle_id": vid})
    oid = r.json()["id"]
    r = await client.get(f"/service-orders/{oid}/status")
    assert r.status_code == 200
    assert r.json()["status"] == "RECEBIDA"


@pytest.mark.asyncio
async def test_public_status_not_found_returns_404(client: AsyncClient):
    r = await client.get("/service-orders/9999/status")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stock_decremented_on_order_creation(auth_client: AsyncClient):
    cid = await _create_client(auth_client)
    vid = await _create_vehicle(auth_client, cid)
    pid = await _create_part(auth_client)
    await auth_client.post("/service-orders", json={
        "vehicle_id": vid,
        "parts": [{"part_id": pid, "quantity": 3}],
    })
    r = await auth_client.get(f"/parts/{pid}")
    assert r.json()["stock_quantity"] == 7
