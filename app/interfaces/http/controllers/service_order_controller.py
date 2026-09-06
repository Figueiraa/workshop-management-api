from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.service_order_dtos import (
    OpenServiceOrderInput,
    OpenServiceOrderItemInput,
    OpenServiceOrderPartInput,
)
from app.application.ports.notifier import NotifierPort
from app.application.use_cases.approve_budget import ApproveBudgetUseCase
from app.application.use_cases.get_average_execution_time import GetAverageExecutionTimeUseCase
from app.application.use_cases.get_service_order import GetServiceOrderUseCase
from app.application.use_cases.list_service_orders import ListServiceOrdersUseCase
from app.application.use_cases.open_service_order import OpenServiceOrderUseCase
from app.application.use_cases.update_service_order_status import UpdateServiceOrderStatusUseCase
from app.domain.value_objects.service_order_status import ServiceOrderStatus
from app.infrastructure.database import get_db
from app.infrastructure.notifications.notifier import build_notifier
from app.infrastructure.observability.metrics import (
    record_budget_approval,
    record_service_order_opened,
    record_status_transition,
)
from app.infrastructure.persistence.gateways.service_order_gateways import (
    SqlAlchemyPartGateway,
    SqlAlchemyServiceTypeGateway,
    SqlAlchemyVehicleGateway,
)
from app.infrastructure.persistence.repositories.client_repository import SqlAlchemyClientRepository
from app.infrastructure.persistence.repositories.service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.service_order_schema import (
    AverageExecutionTimeResponse,
    BudgetApprovalRequest,
    ServiceOrderCreate,
    ServiceOrderResponse,
    ServiceOrderSummary,
    ServiceOrderUpdateStatus,
)

router = APIRouter(prefix="/service-orders", tags=["Ordens de Serviço"])


def _repository(db: AsyncSession) -> SqlAlchemyServiceOrderRepository:
    return SqlAlchemyServiceOrderRepository(db)


def _notifier() -> NotifierPort:
    return build_notifier()


@router.get("", response_model=list[ServiceOrderSummary])
async def list_orders(
    status: ServiceOrderStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ListServiceOrdersUseCase(_repository(db)).execute(status)


@router.get("/metrics/average-execution-time", response_model=AverageExecutionTimeResponse)
async def average_execution_time(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await GetAverageExecutionTimeUseCase(_repository(db)).execute()


@router.get("/{order_id}", response_model=ServiceOrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await GetServiceOrderUseCase(_repository(db)).execute(order_id)


@router.post("", response_model=ServiceOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: ServiceOrderCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = OpenServiceOrderUseCase(
        _repository(db),
        SqlAlchemyVehicleGateway(db),
        SqlAlchemyServiceTypeGateway(db),
        SqlAlchemyPartGateway(db),
    )
    payload = OpenServiceOrderInput(
        vehicle_id=data.vehicle_id,
        notes=data.notes,
        items=[
            OpenServiceOrderItemInput(service_type_id=item.service_type_id, quantity=item.quantity)
            for item in data.items
        ],
        parts=[
            OpenServiceOrderPartInput(part_id=part.part_id, quantity=part.quantity) for part in data.parts
        ],
    )
    order = await use_case.execute(payload)
    # Métricas de negócio são registradas no adapter: o caso de uso permanece
    # livre de dependências de infraestrutura (regra de dependência).
    record_service_order_opened()
    record_status_transition(order.status.value)
    return order


@router.patch("/{order_id}/status", response_model=ServiceOrderResponse)
async def update_status(
    order_id: int,
    data: ServiceOrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = UpdateServiceOrderStatusUseCase(_repository(db), SqlAlchemyClientRepository(db), _notifier())
    order = await use_case.execute(order_id, data.status)
    record_status_transition(order.status.value)
    return order


@router.post("/{order_id}/budget-approval", response_model=ServiceOrderResponse)
async def budget_approval(
    order_id: int,
    data: BudgetApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    """Recebe notificações externas de aprovação ou recusa do orçamento do cliente."""
    use_case = ApproveBudgetUseCase(
        _repository(db),
        SqlAlchemyPartGateway(db),
        SqlAlchemyClientRepository(db),
        _notifier(),
    )
    order = await use_case.execute(order_id, data.approved)
    record_budget_approval(data.approved)
    record_status_transition(order.status.value)
    return order


@router.get("/{order_id}/status", response_model=dict)
async def get_order_status(order_id: int, db: AsyncSession = Depends(get_db)):
    """Rota pública para clientes consultarem o status da OS."""
    order = await GetServiceOrderUseCase(_repository(db)).execute(order_id)
    return {"number": order.number, "status": order.status}
