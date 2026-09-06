import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.routing import Match

from app.infrastructure.logging_config import request_id_ctx
from app.infrastructure.observability.metrics import (
    http_exceptions_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
)

# Endpoint de exposição das métricas — não é instrumentado a si mesmo.
METRICS_PATH = "/metrics"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Gera/propaga um X-Request-ID por requisição para rastreio e correlação de logs."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


# Rotas da documentação interativa (Swagger UI / ReDoc): carregam assets de CDN e
# usam script inline, então a CSP restritiva não se aplica a elas.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona cabeçalhos de segurança recomendados (OWASP) às respostas da API."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if not request.url.path.startswith(_DOCS_PATHS):
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Instrumenta cada requisição HTTP (contagem, duração e concorrência).

    O rótulo `endpoint` usa o *template* da rota (`/api/v1/service-orders/{order_id}`)
    e não a URL concreta, para não explodir a cardinalidade das séries temporais
    com um label por identificador. Requisições sem rota correspondente (404)
    são agrupadas em `unmatched`.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path == METRICS_PATH:
            return await call_next(request)

        method = request.method
        endpoint = _endpoint_label(request)
        in_progress = http_requests_in_progress.labels(method=method, endpoint=endpoint)
        duration = http_request_duration_seconds.labels(method=method, endpoint=endpoint)

        in_progress.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            http_exceptions_total.labels(
                method=method, endpoint=endpoint, exception=type(exc).__name__
            ).inc()
            # A exceção vira 500 no handler global; contabiliza como tal.
            http_requests_total.labels(method=method, endpoint=endpoint, status_code="500").inc()
            raise
        else:
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=str(response.status_code)
            ).inc()
            return response
        finally:
            duration.observe(time.perf_counter() - start)
            in_progress.dec()


def _endpoint_label(request: Request) -> str:
    """Resolve o template da rota que atenderá a requisição.

    O roteamento do Starlette só grava `scope["route"]` depois do middleware, então
    aqui repetimos o match contra as rotas da aplicação para já rotular a métrica de
    requisições em andamento com um valor de baixa cardinalidade.
    """
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match is not Match.NONE:
            return getattr(route, "path", request.url.path)
    return "unmatched"
