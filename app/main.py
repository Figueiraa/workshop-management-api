from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.controllers import (
    auth_controller,
    client_controller,
    part_controller,
    service_order_controller,
    service_type_controller,
    vehicle_controller,
)
from app.core.database import Base, engine
from app.exceptions.domain_exceptions import (
    BusinessRuleError,
    ConflictError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    NotFoundError,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Workshop Management API",
    description="Sistema Integrado de Oficina Mecânica — MVP",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(_: Request, exc: ConflictError):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(_: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})


@app.exception_handler(InsufficientStockError)
async def insufficient_stock_handler(_: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})


@app.exception_handler(InvalidStatusTransitionError)
async def invalid_transition_handler(_: Request, exc: InvalidStatusTransitionError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})


app.include_router(auth_controller.router)
app.include_router(client_controller.router)
app.include_router(vehicle_controller.router)
app.include_router(service_type_controller.router)
app.include_router(part_controller.router)
app.include_router(service_order_controller.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
