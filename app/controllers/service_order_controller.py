from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.exceptions.domain_exceptions import InsufficientStockError, InvalidStatusTransitionError, NotFoundError
from app.models.service_order_model import ServiceOrderStatus
from app.schemas.service_order_schema import (
    AverageExecutionTimeResponse,
    ServiceOrderCreate,
    ServiceOrderResponse,
    ServiceOrderSummary,
    ServiceOrderUpdateStatus,
)
from app.services.service_order_service import ServiceOrderService

router = APIRouter(prefix="/service-orders", tags=["Ordens de Serviço"])


@router.get("", response_model=list[ServiceOrderSummary])
async def list_orders(
    status: ServiceOrderStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    svc = ServiceOrderService(db)
    if status:
        return await svc.list_by_status(status)
    return await svc.list_all()


@router.get("/metrics/average-execution-time", response_model=AverageExecutionTimeResponse)
async def average_execution_time(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ServiceOrderService(db).get_average_execution_time()


@router.get("/{order_id}", response_model=ServiceOrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    try:
        return await ServiceOrderService(db).get_by_id(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ServiceOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: ServiceOrderCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await ServiceOrderService(db).create(data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch("/{order_id}/status", response_model=ServiceOrderResponse)
async def update_status(
    order_id: int,
    data: ServiceOrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await ServiceOrderService(db).update_status(order_id, data.status)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{order_id}/status", response_model=dict)
async def get_order_status(order_id: int, db: AsyncSession = Depends(get_db)):
    """Rota pública para clientes consultarem o status da OS."""
    try:
        order = await ServiceOrderService(db).get_by_id(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"number": order.number, "status": order.status}
