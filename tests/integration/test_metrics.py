"""Testes de ponta a ponta da exposição de métricas (`GET /metrics`).

Cobrem o middleware de instrumentação HTTP e as métricas de negócio registradas
pelos controllers ao abrir OS, mudar status e responder orçamento.
"""

from prometheus_client.parser import text_string_to_metric_families


def _sample(payload: str, name: str, labels: dict[str, str] | None = None) -> float:
    """Valor de uma amostra do texto de exposição (0.0 quando a série não existe)."""
    for family in text_string_to_metric_families(payload):
        for sample in family.samples:
            if sample.name == name and (labels is None or labels.items() <= sample.labels.items()):
                return sample.value
    return 0.0


async def _scrape(client) -> str:
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    return resp.text


async def _criar_os(auth_client) -> int:
    """Cria cliente, veículo, serviço e peça e abre uma OS; devolve o id da OS."""
    cliente = await auth_client.post(
        "/api/v1/clients",
        json={"name": "Maria", "cpf_cnpj": "529.982.247-25", "email": "maria@teste.com"},
    )
    client_id = cliente.json()["id"]

    veiculo = await auth_client.post(
        "/api/v1/vehicles",
        json={
            "client_id": client_id,
            "plate": "ABC1D23",
            "brand": "Fiat",
            "model": "Uno",
            "year": 2020,
        },
    )
    vehicle_id = veiculo.json()["id"]

    servico = await auth_client.post(
        "/api/v1/service-types",
        json={"name": "Troca de oleo", "price": 150.0, "estimated_duration_minutes": 30},
    )
    peca = await auth_client.post(
        "/api/v1/parts", json={"name": "Filtro", "unit_price": 30.0, "stock_quantity": 10}
    )

    os_resp = await auth_client.post(
        "/api/v1/service-orders",
        json={
            "vehicle_id": vehicle_id,
            "notes": "revisao",
            "items": [{"service_type_id": servico.json()["id"], "quantity": 1}],
            "parts": [{"part_id": peca.json()["id"], "quantity": 1}],
        },
    )
    assert os_resp.status_code == 201
    return os_resp.json()["id"]


class TestEndpointDeMetricas:
    async def test_responde_200_no_formato_prometheus(self, client):
        resp = await client.get("/metrics")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert "# TYPE workshop_http_requests_total counter" in resp.text

    async def test_expoe_metadados_da_aplicacao(self, client):
        payload = await _scrape(client)

        assert _sample(payload, "workshop_app_info", {"name": "workshop-management-api"}) == 1

    async def test_endpoint_de_metricas_nao_se_instrumenta(self, client):
        await client.get("/metrics")
        payload = await _scrape(client)

        assert _sample(payload, "workshop_http_requests_total", {"endpoint": "/metrics"}) == 0


class TestMetricasHttp:
    async def test_conta_requisicao_bem_sucedida(self, client):
        antes = _sample(
            await _scrape(client),
            "workshop_http_requests_total",
            {"method": "GET", "endpoint": "/health", "status_code": "200"},
        )

        await client.get("/health")

        depois = _sample(
            await _scrape(client),
            "workshop_http_requests_total",
            {"method": "GET", "endpoint": "/health", "status_code": "200"},
        )
        assert depois == antes + 1

    async def test_registra_duracao_da_requisicao(self, client):
        await client.get("/health")
        payload = await _scrape(client)

        count = _sample(
            payload,
            "workshop_http_request_duration_seconds_count",
            {"method": "GET", "endpoint": "/health"},
        )
        assert count >= 1

    async def test_usa_o_template_da_rota_e_nao_a_url_concreta(self, auth_client):
        order_id = await _criar_os(auth_client)
        await auth_client.get(f"/api/v1/service-orders/{order_id}")
        payload = await _scrape(auth_client)

        # A série deve usar o template da rota, para não explodir a cardinalidade.
        assert (
            _sample(
                payload,
                "workshop_http_requests_total",
                {"endpoint": "/api/v1/service-orders/{order_id}"},
            )
            >= 1
        )
        assert f"/api/v1/service-orders/{order_id}" not in payload

    async def test_erro_de_cliente_e_contabilizado_com_o_status(self, client):
        await client.get("/api/v1/service-orders/999999")
        payload = await _scrape(client)

        assert (
            _sample(
                payload,
                "workshop_http_requests_total",
                {"endpoint": "/api/v1/service-orders/{order_id}", "status_code": "401"},
            )
            >= 1
        )

    async def test_rota_inexistente_e_agrupada_em_unmatched(self, client):
        await client.get("/rota-que-nao-existe")
        payload = await _scrape(client)

        assert _sample(payload, "workshop_http_requests_total", {"endpoint": "unmatched"}) >= 1

    async def test_gauge_de_requisicoes_em_andamento_volta_a_zero(self, client):
        await client.get("/health")
        payload = await _scrape(client)

        assert (
            _sample(
                payload,
                "workshop_http_requests_in_progress",
                {"method": "GET", "endpoint": "/health"},
            )
            == 0
        )


class TestMetricasDeNegocio:
    async def test_abertura_de_os_incrementa_contador(self, auth_client):
        antes = _sample(await _scrape(auth_client), "workshop_service_orders_opened_total")

        await _criar_os(auth_client)

        depois = _sample(await _scrape(auth_client), "workshop_service_orders_opened_total")
        assert depois == antes + 1

    async def test_mudanca_de_status_incrementa_transicoes(self, auth_client):
        order_id = await _criar_os(auth_client)
        antes = _sample(
            await _scrape(auth_client),
            "workshop_service_order_status_transitions_total",
            {"status": "EM_DIAGNOSTICO"},
        )

        resp = await auth_client.patch(
            f"/api/v1/service-orders/{order_id}/status", json={"status": "EM_DIAGNOSTICO"}
        )
        assert resp.status_code == 200

        depois = _sample(
            await _scrape(auth_client),
            "workshop_service_order_status_transitions_total",
            {"status": "EM_DIAGNOSTICO"},
        )
        assert depois == antes + 1

    async def test_aprovacao_de_orcamento_incrementa_contador(self, auth_client):
        order_id = await _criar_os(auth_client)
        for status in ("EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO"):
            await auth_client.patch(
                f"/api/v1/service-orders/{order_id}/status", json={"status": status}
            )

        antes = _sample(
            await _scrape(auth_client), "workshop_budget_approvals_total", {"result": "approved"}
        )

        resp = await auth_client.post(
            f"/api/v1/service-orders/{order_id}/budget-approval", json={"approved": True}
        )
        assert resp.status_code == 200

        depois = _sample(
            await _scrape(auth_client), "workshop_budget_approvals_total", {"result": "approved"}
        )
        assert depois == antes + 1

    async def test_recusa_de_orcamento_incrementa_contador(self, auth_client):
        order_id = await _criar_os(auth_client)
        for status in ("EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO"):
            await auth_client.patch(
                f"/api/v1/service-orders/{order_id}/status", json={"status": status}
            )

        antes = _sample(
            await _scrape(auth_client), "workshop_budget_approvals_total", {"result": "refused"}
        )

        await auth_client.post(
            f"/api/v1/service-orders/{order_id}/budget-approval", json={"approved": False}
        )

        depois = _sample(
            await _scrape(auth_client), "workshop_budget_approvals_total", {"result": "refused"}
        )
        assert depois == antes + 1

    async def test_notificacao_de_status_e_contabilizada(self, auth_client):
        order_id = await _criar_os(auth_client)
        antes = _sample(
            await _scrape(auth_client),
            "workshop_notifications_total",
            {"channel": "log", "result": "sent"},
        )

        await auth_client.patch(
            f"/api/v1/service-orders/{order_id}/status", json={"status": "EM_DIAGNOSTICO"}
        )

        depois = _sample(
            await _scrape(auth_client),
            "workshop_notifications_total",
            {"channel": "log", "result": "sent"},
        )
        assert depois == antes + 1
