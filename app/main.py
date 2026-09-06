from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Importa o pacote de modelos para registrar todas as tabelas no metadata do SQLAlchemy.
import app.infrastructure.persistence.models  # noqa: F401
from app.infrastructure.config import settings
from app.infrastructure.database import Base, engine, get_db
from app.infrastructure.logging_config import setup_logging
from app.infrastructure.observability.metrics import (
    CONTENT_TYPE_PROMETHEUS,
    render_latest,
    set_app_info,
)
from app.interfaces.http.controllers import (
    auth_controller,
    client_controller,
    part_controller,
    service_order_controller,
    service_type_controller,
    vehicle_controller,
)
from app.interfaces.http.exception_handlers import register_exception_handlers
from app.interfaces.http.middleware import (
    MetricsMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)

setup_logging(settings.LOG_LEVEL)

API_V1 = "/api/v1"
APP_NAME = "workshop-management-api"
APP_VERSION = "2.1.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Workshop Management API",
    description="Sistema Integrado de Oficina Mecânica — Clean Architecture",
    version=APP_VERSION,
    lifespan=lifespan,
)

set_app_info(name=APP_NAME, version=APP_VERSION)

# Middlewares (o último adicionado é o mais externo).
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

register_exception_handlers(app)

for controller in (
    auth_controller,
    client_controller,
    vehicle_controller,
    service_type_controller,
    part_controller,
    service_order_controller,
):
    app.include_router(controller.router, prefix=API_V1)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


@app.get("/health/live", tags=["Health"])
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected"},
        )
    return {"status": "ready", "database": "connected"}


@app.get(
    "/metrics",
    tags=["Observabilidade"],
    summary="Métricas no formato Prometheus",
    response_class=Response,
    responses={200: {"content": {CONTENT_TYPE_PROMETHEUS: {}}}},
)
async def metrics() -> Response:
    """Endpoint de scrape do Prometheus (métricas técnicas RED + métricas de negócio)."""
    return Response(content=render_latest(), media_type=CONTENT_TYPE_PROMETHEUS)
