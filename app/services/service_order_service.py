from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.domain_exceptions import InsufficientStockError, InvalidStatusTransitionError, NotFoundError
from app.models.service_order_model import (
    VALID_TRANSITIONS,
    ServiceOrder,
    ServiceOrderItem,
    ServiceOrderPart,
    ServiceOrderStatus,
)
from app.repositories.part_repository import PartRepository
from app.repositories.service_order_repository import ServiceOrderRepository
from app.repositories.service_type_repository import ServiceTypeRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.service_order_schema import AverageExecutionTimeResponse, ServiceOrderCreate


class ServiceOrderService:
    def __init__(self, db: AsyncSession):
        self._repo = ServiceOrderRepository(db)
        self._vehicle_repo = VehicleRepository(db)
        self._service_type_repo = ServiceTypeRepository(db)
        self._part_repo = PartRepository(db)

    async def list_all(self) -> list[ServiceOrder]:
        return await self._repo.get_all()

    async def get_by_id(self, order_id: int) -> ServiceOrder:
        order = await self._repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Ordem de serviço", order_id)
        return order

    async def list_by_status(self, status: ServiceOrderStatus) -> list[ServiceOrder]:
        return await self._repo.get_by_status(status)

    async def create(self, data: ServiceOrderCreate) -> ServiceOrder:
        vehicle = await self._vehicle_repo.get_by_id(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", data.vehicle_id)

        total = 0.0
        items: list[ServiceOrderItem] = []
        for item_input in data.items:
            svc = await self._service_type_repo.get_by_id(item_input.service_type_id)
            if not svc:
                raise NotFoundError("Serviço", item_input.service_type_id)
            price = float(svc.price)
            total += price * item_input.quantity
            items.append(
                ServiceOrderItem(
                    service_type_id=svc.id,
                    quantity=item_input.quantity,
                    unit_price=price,
                )
            )

        order_parts: list[ServiceOrderPart] = []
        for part_input in data.parts:
            part = await self._part_repo.get_by_id(part_input.part_id)
            if not part:
                raise NotFoundError("Peça/Insumo", part_input.part_id)
            if part.stock_quantity < part_input.quantity:
                raise InsufficientStockError(part.name, part.stock_quantity, part_input.quantity)
            price = float(part.unit_price)
            total += price * part_input.quantity
            order_parts.append(
                ServiceOrderPart(
                    part_id=part.id,
                    quantity=part_input.quantity,
                    unit_price=price,
                )
            )

        count = await self._repo.count_today()
        now = datetime.now(timezone.utc)
        number = f"OS{now.strftime('%Y%m%d')}{count + 1:04d}"

        order = ServiceOrder(
            number=number,
            vehicle_id=vehicle.id,
            client_id=vehicle.client_id,
            notes=data.notes,
            total_budget=total,
            items=items,
            parts=order_parts,
        )

        for part_input in data.parts:
            part = await self._part_repo.get_by_id(part_input.part_id)
            part.stock_quantity -= part_input.quantity  # type: ignore[operator]

        return await self._repo.create(order)

    async def update_status(self, order_id: int, new_status: ServiceOrderStatus) -> ServiceOrder:
        order = await self.get_by_id(order_id)
        allowed = VALID_TRANSITIONS[order.status]
        if new_status not in allowed:
            raise InvalidStatusTransitionError(order.status.value, new_status.value)

        now = datetime.now(timezone.utc)
        if new_status == ServiceOrderStatus.EM_EXECUCAO:
            order.started_at = now
        elif new_status == ServiceOrderStatus.FINALIZADA:
            order.completed_at = now
        elif new_status == ServiceOrderStatus.ENTREGUE:
            order.delivered_at = now

        order.status = new_status
        return await self._repo.update(order)

    async def get_average_execution_time(self) -> AverageExecutionTimeResponse:
        orders = await self._repo.get_completed_with_times()
        if not orders:
            return AverageExecutionTimeResponse(average_minutes=None, total_completed=0)

        total_minutes = sum(
            (o.completed_at - o.started_at).total_seconds() / 60 for o in orders  # type: ignore[operator]
        )
        return AverageExecutionTimeResponse(
            average_minutes=round(total_minutes / len(orders), 2),
            total_completed=len(orders),
        )
