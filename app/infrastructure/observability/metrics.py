"""Métricas de aplicação no formato Prometheus (OpenMetrics).

Concentra num único módulo os coletores expostos em `GET /metrics`. As métricas
se dividem em duas famílias:

* **Técnicas (RED):** taxa, erros e duração das requisições HTTP — alimentadas
  pelo `MetricsMiddleware` (camada de interface).
* **De negócio:** eventos do domínio da oficina (OS abertas, transições de
  status, orçamentos, notificações) — registrados pelos adapters que executam
  o caso de uso, mantendo `domain` e `application` livres de infraestrutura.
"""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

# Registry próprio (em vez do global) para que os testes possam inspecionar e
# reiniciar os coletores sem interferência de bibliotecas de terceiros.
REGISTRY = CollectorRegistry(auto_describe=True)

CONTENT_TYPE_PROMETHEUS = "text/plain; version=0.0.4; charset=utf-8"

# Faixas em segundos alinhadas ao SLO da API (p95 < 300 ms).
_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

# ─── Métricas técnicas (RED: Rate, Errors, Duration) ─────────────────────────

http_requests_total = Counter(
    "workshop_http_requests_total",
    "Total de requisições HTTP recebidas pela API.",
    labelnames=("method", "endpoint", "status_code"),
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "workshop_http_request_duration_seconds",
    "Duração das requisições HTTP em segundos.",
    labelnames=("method", "endpoint"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

http_requests_in_progress = Gauge(
    "workshop_http_requests_in_progress",
    "Requisições HTTP sendo processadas neste momento.",
    labelnames=("method", "endpoint"),
    registry=REGISTRY,
)

http_exceptions_total = Counter(
    "workshop_http_exceptions_total",
    "Exceções não tratadas propagadas até o middleware.",
    labelnames=("method", "endpoint", "exception"),
    registry=REGISTRY,
)

# ─── Métricas de negócio ─────────────────────────────────────────────────────

service_orders_opened_total = Counter(
    "workshop_service_orders_opened_total",
    "Ordens de serviço abertas.",
    registry=REGISTRY,
)

service_order_status_transitions_total = Counter(
    "workshop_service_order_status_transitions_total",
    "Transições de status de ordens de serviço, por status de destino.",
    labelnames=("status",),
    registry=REGISTRY,
)

budget_approvals_total = Counter(
    "workshop_budget_approvals_total",
    "Respostas de orçamento recebidas do cliente.",
    labelnames=("result",),  # approved | refused
    registry=REGISTRY,
)

notifications_total = Counter(
    "workshop_notifications_total",
    "Notificações de mudança de status enviadas ao cliente.",
    labelnames=("channel", "result"),  # channel: email|log — result: sent|skipped|failed
    registry=REGISTRY,
)

app_info = Gauge(
    "workshop_app_info",
    "Metadados da aplicação em execução (valor sempre 1).",
    labelnames=("version", "name"),
    registry=REGISTRY,
)


# ─── Helpers usados pelos adapters ───────────────────────────────────────────


def set_app_info(name: str, version: str) -> None:
    app_info.labels(version=version, name=name).set(1)


def record_service_order_opened() -> None:
    service_orders_opened_total.inc()


def record_status_transition(status: str) -> None:
    service_order_status_transitions_total.labels(status=status).inc()


def record_budget_approval(approved: bool) -> None:
    budget_approvals_total.labels(result="approved" if approved else "refused").inc()


def record_notification(channel: str, result: str) -> None:
    notifications_total.labels(channel=channel, result=result).inc()


def render_latest() -> bytes:
    """Serializa o snapshot atual das métricas no formato de exposição Prometheus."""
    return generate_latest(REGISTRY)


__all__ = [
    "CONTENT_TYPE_PROMETHEUS",
    "REGISTRY",
    "budget_approvals_total",
    "http_exceptions_total",
    "http_request_duration_seconds",
    "http_requests_in_progress",
    "http_requests_total",
    "notifications_total",
    "record_budget_approval",
    "record_notification",
    "record_service_order_opened",
    "record_status_transition",
    "render_latest",
    "service_order_status_transitions_total",
    "service_orders_opened_total",
    "set_app_info",
]
