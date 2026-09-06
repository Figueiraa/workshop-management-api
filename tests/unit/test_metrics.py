"""Testes dos coletores de métricas e dos helpers usados pelos adapters."""

from prometheus_client.parser import text_string_to_metric_families

from app.infrastructure.observability import metrics


def _sample(payload: str, name: str, labels: dict[str, str] | None = None) -> float | None:
    """Extrai o valor de uma amostra do texto de exposição do Prometheus."""
    for family in text_string_to_metric_families(payload):
        for sample in family.samples:
            if sample.name == name and (labels is None or labels.items() <= sample.labels.items()):
                return sample.value
    return None


class TestRenderLatest:
    def test_expoe_texto_no_formato_prometheus(self):
        payload = metrics.render_latest().decode("utf-8")

        assert "# HELP workshop_http_requests_total" in payload
        assert "# TYPE workshop_http_requests_total counter" in payload

    def test_expoe_todas_as_familias_de_metricas(self):
        payload = metrics.render_latest().decode("utf-8")

        for name in (
            "workshop_http_requests_total",
            "workshop_http_request_duration_seconds",
            "workshop_http_requests_in_progress",
            "workshop_http_exceptions_total",
            "workshop_service_orders_opened_total",
            "workshop_service_order_status_transitions_total",
            "workshop_budget_approvals_total",
            "workshop_notifications_total",
            "workshop_app_info",
        ):
            assert f"# HELP {name}" in payload, f"métrica ausente: {name}"


class TestAppInfo:
    def test_registra_nome_e_versao(self):
        metrics.set_app_info(name="workshop-teste", version="9.9.9")
        payload = metrics.render_latest().decode("utf-8")

        assert (
            _sample(payload, "workshop_app_info", {"name": "workshop-teste", "version": "9.9.9"}) == 1
        )


class TestMetricasDeNegocio:
    def test_conta_abertura_de_os(self):
        antes = metrics.service_orders_opened_total._value.get()
        metrics.record_service_order_opened()
        assert metrics.service_orders_opened_total._value.get() == antes + 1

    def test_conta_transicao_por_status(self):
        contador = metrics.service_order_status_transitions_total.labels(status="EM_EXECUCAO")
        antes = contador._value.get()
        metrics.record_status_transition("EM_EXECUCAO")
        assert contador._value.get() == antes + 1

    def test_orcamento_aprovado_e_recusado_usam_labels_distintos(self):
        aprovado = metrics.budget_approvals_total.labels(result="approved")
        recusado = metrics.budget_approvals_total.labels(result="refused")
        antes_aprovado, antes_recusado = aprovado._value.get(), recusado._value.get()

        metrics.record_budget_approval(True)
        metrics.record_budget_approval(False)

        assert aprovado._value.get() == antes_aprovado + 1
        assert recusado._value.get() == antes_recusado + 1

    def test_conta_notificacao_por_canal_e_resultado(self):
        contador = metrics.notifications_total.labels(channel="email", result="sent")
        antes = contador._value.get()
        metrics.record_notification(channel="email", result="sent")
        assert contador._value.get() == antes + 1
