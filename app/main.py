from contextlib import asynccontextmanager

from fastapi import FastAPI

# Importa o pacote de modelos para registrar todas as tabelas no metadata do SQLAlchemy.
import app.infrastructure.persistence.models  # noqa: F401
from app.infrastructure.database import Base, engine
from app.interfaces.http.controllers import (
    auth_controller,
    client_controller,
    part_controller,
    service_order_controller,
    service_type_controller,
    vehicle_controller,
)
from app.interfaces.http.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Workshop Management API",
    description="Sistema Integrado de Oficina Mecânica — Clean Architecture",
    version="2.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_controller.router)
app.include_router(client_controller.router)
app.include_router(vehicle_controller.router)
app.include_router(service_type_controller.router)
app.include_router(part_controller.router)
app.include_router(service_order_controller.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
