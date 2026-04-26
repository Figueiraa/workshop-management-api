from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service_order_model import ServiceOrder, ServiceOrderStatus


class ServiceOrderRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    def _with_relations(self):
        return select(ServiceOrder).options(
            selectinload(ServiceOrder.items),
            selectinload(ServiceOrder.parts),
        )

    async def get_all(self) -> list[ServiceOrder]:
        result = await self._db.execute(self._with_relations().order_by(ServiceOrder.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, order_id: int) -> ServiceOrder | None:
        result = await self._db.execute(self._with_relations().where(ServiceOrder.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_number(self, number: str) -> ServiceOrder | None:
        result = await self._db.execute(self._with_relations().where(ServiceOrder.number == number))
        return result.scalar_one_or_none()

    async def get_by_status(self, status: ServiceOrderStatus) -> list[ServiceOrder]:
        result = await self._db.execute(self._with_relations().where(ServiceOrder.status == status))
        return list(result.scalars().all())

    async def count_today(self) -> int:
        result = await self._db.execute(select(func.count(ServiceOrder.id)))
        return result.scalar_one()

    async def create(self, order: ServiceOrder) -> ServiceOrder:
        self._db.add(order)
        await self._db.commit()
        result = await self._db.execute(self._with_relations().where(ServiceOrder.id == order.id))
        return result.scalar_one()

    async def update(self, order: ServiceOrder) -> ServiceOrder:
        await self._db.commit()
        result = await self._db.execute(self._with_relations().where(ServiceOrder.id == order.id))
        return result.scalar_one()

    async def get_completed_with_times(self) -> list[ServiceOrder]:
        result = await self._db.execute(
            select(ServiceOrder).where(
                ServiceOrder.status == ServiceOrderStatus.ENTREGUE,
                ServiceOrder.started_at.is_not(None),
                ServiceOrder.completed_at.is_not(None),
            )
        )
        return list(result.scalars().all())
