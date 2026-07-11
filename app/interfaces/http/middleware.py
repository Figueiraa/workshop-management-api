import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.infrastructure.logging_config import request_id_ctx


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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona cabeçalhos de segurança recomendados (OWASP) a todas as respostas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
