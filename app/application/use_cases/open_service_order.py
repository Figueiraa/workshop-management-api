from datetime import UTC, datetime

from app.application.dtos.service_order_dtos import OpenServiceOrderInput
from app.application.ports.gateways import PartGatewayPort, ServiceTypeGatewayPort, VehicleGatewayPort
from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder, ServiceOrderItem, ServiceOrderPart
from app.domain.exceptions.domain_exceptions import InsufficientStockError, NotFoundError


class OpenServiceOrderUseCase:
    """Abre uma Ordem de Serviço a partir de veículo, serviços e peças."""

    def __init__(
        self,
        repository: ServiceOrderRepositoryPort,
        vehicle_gateway: VehicleGatewayPort,
        service_type_gateway: ServiceTypeGatewayPort,
        part_gateway: PartGatewayPort,
    ):
        self._repo = repository
        self._vehicles = vehicle_gateway
        self._service_types = service_type_gateway
        self._parts = part_gateway

    async def execute(self, data: OpenServiceOrderInput) -> ServiceOrder:
        vehicle = await self._vehicles.get_by_id(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", data.vehicle_id)

        total = 0.0
        items: list[ServiceOrderItem] = []
        for item_input in data.items:
            service_type = await self._service_types.get_by_id(item_input.service_type_id)
            if not service_type:
                raise NotFoundError("Serviço", item_input.service_type_id)
            total += service_type.price * item_input.quantity
            items.append(
                ServiceOrderItem(
                    service_type_id=service_type.id,
                    quantity=item_input.quantity,
                    unit_price=service_type.price,
                )
            )

        parts: list[ServiceOrderPart] = []
        stock_decrements: list[tuple[int, int]] = []
        for part_input in data.parts:
            part = await self._parts.get_by_id(part_input.part_id)
            if not part:
                raise NotFoundError("Peça/Insumo", part_input.part_id)
            if part.stock_quantity < part_input.quantity:
                raise InsufficientStockError(part.name, part.stock_quantity, part_input.quantity)
            total += part.unit_price * part_input.quantity
            parts.append(
                ServiceOrderPart(
                    part_id=part.id,
                    quantity=part_input.quantity,
                    unit_price=part.unit_price,
                )
            )
            stock_decrements.append((part.id, part_input.quantity))

        count = await self._repo.count()
        now = datetime.now(UTC)
        number = f"OS{now.strftime('%Y%m%d')}{count + 1:04d}"

        order = ServiceOrder(
            number=number,
            vehicle_id=vehicle.id,
            client_id=vehicle.client_id,
            total_budget=total,
            notes=data.notes,
            items=items,
            parts=parts,
        )

        for part_id, quantity in stock_decrements:
            await self._parts.decrement_stock(part_id, quantity)

        return await self._repo.add(order)
