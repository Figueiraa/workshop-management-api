from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder
from app.domain.value_objects.service_order_status import TERMINAL_STATUSES, ServiceOrderStatus
from app.infrastructure.persistence.mappers.service_order_mapper import to_domain, to_model
from app.infrastructure.persistence.models.service_order_model import ServiceOrder as ServiceOrderModel

# Prioridade de exibição na listagem: Em Execução > Aguardando Aprovação > Diagnóstico > Recebida.
_STATUS_PRIORITY = case(
    (ServiceOrderModel.status == ServiceOrderStatus.EM_EXECUCAO, 1),
    (ServiceOrderModel.status == ServiceOrderStatus.AGUARDANDO_APROVACAO, 2),
    (ServiceOrderModel.status == ServiceOrderStatus.EM_DIAGNOSTICO, 3),
    (ServiceOrderModel.status == ServiceOrderStatus.RECEBIDA, 4),
    else_=99,
)


class SqlAlchemyServiceOrderRepository(ServiceOrderRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    def _with_relations(self):
        return select(ServiceOrderModel).options(
            selectinload(ServiceOrderModel.items),
            selectinload(ServiceOrderModel.parts),
        )

    async def _get_model(self, order_id: int) -> ServiceOrderModel | None:
        result = await self._db.execute(self._with_relations().where(ServiceOrderModel.id == order_id))
        return result.scalar_one_or_none()

    async def add(self, order: ServiceOrder) -> ServiceOrder:
        model = to_model(order)
        self._db.add(model)
        await self._db.commit()
        persisted = await self._get_model(model.id)
        return to_domain(persisted)

    async def get_by_id(self, order_id: int) -> ServiceOrder | None:
        model = await self._get_model(order_id)
        return to_domain(model) if model else None

    async def list_open_ordered(self) -> list[ServiceOrder]:
        query = (
            self._with_relations()
            .where(ServiceOrderModel.status.notin_(TERMINAL_STATUSES))
            .order_by(_STATUS_PRIORITY, ServiceOrderModel.created_at.asc(), ServiceOrderModel.id.asc())
        )
        result = await self._db.execute(query)
        return [to_domain(model) for model in result.scalars().all()]

    async def get_by_status(self, status: ServiceOrderStatus) -> list[ServiceOrder]:
        result = await self._db.execute(self._with_relations().where(ServiceOrderModel.status == status))
        return [to_domain(model) for model in result.scalars().all()]

    async def update(self, order: ServiceOrder) -> ServiceOrder:
        model = await self._get_model(order.id)
        model.status = order.status
        model.notes = order.notes
        model.total_budget = order.total_budget
        model.started_at = order.started_at
        model.completed_at = order.completed_at
        model.delivered_at = order.delivered_at
        await self._db.commit()
        refreshed = await self._get_model(order.id)
        return to_domain(refreshed)

    async def count(self) -> int:
        result = await self._db.execute(select(func.count(ServiceOrderModel.id)))
        return result.scalar_one()

    async def get_completed_with_times(self) -> list[ServiceOrder]:
        result = await self._db.execute(
            self._with_relations().where(
                ServiceOrderModel.status == ServiceOrderStatus.ENTREGUE,
                ServiceOrderModel.started_at.is_not(None),
                ServiceOrderModel.completed_at.is_not(None),
            )
        )
        return [to_domain(model) for model in result.scalars().all()]
