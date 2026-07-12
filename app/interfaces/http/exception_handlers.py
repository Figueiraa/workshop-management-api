from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions.domain_exceptions import (
    BusinessRuleError,
    ConflictError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    NotFoundError,
    UnauthorizedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Mapeia as exceções de domínio para respostas HTTP (camada de interface)."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_: Request, exc: ConflictError):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(_: Request, exc: BusinessRuleError):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(_: Request, exc: InsufficientStockError):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})

    @app.exception_handler(InvalidStatusTransitionError)
    async def invalid_transition_handler(_: Request, exc: InvalidStatusTransitionError):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})
