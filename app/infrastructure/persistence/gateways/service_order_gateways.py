from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.gateways import (
    PartGatewayPort,
    PartRef,
    ServiceTypeGatewayPort,
    ServiceTypeRef,
    VehicleGatewayPort,
    VehicleRef,
)
from app.infrastructure.persistence.models.part_model import Part
from app.infrastructure.persistence.models.service_type_model import ServiceType
from app.infrastructure.persistence.models.vehicle_model import Vehicle


class SqlAlchemyVehicleGateway(VehicleGatewayPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, vehicle_id: int) -> VehicleRef | None:
        result = await self._db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
        vehicle = result.scalar_one_or_none()
        return VehicleRef(id=vehicle.id, client_id=vehicle.client_id) if vehicle else None


class SqlAlchemyServiceTypeGateway(ServiceTypeGatewayPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, service_type_id: int) -> ServiceTypeRef | None:
        result = await self._db.execute(select(ServiceType).where(ServiceType.id == service_type_id))
        service_type = result.scalar_one_or_none()
        return ServiceTypeRef(id=service_type.id, price=float(service_type.price)) if service_type else None


class SqlAlchemyPartGateway(PartGatewayPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, part_id: int) -> PartRef | None:
        result = await self._db.execute(select(Part).where(Part.id == part_id))
        part = result.scalar_one_or_none()
        if not part:
            return None
        return PartRef(
            id=part.id,
            name=part.name,
            unit_price=float(part.unit_price),
            stock_quantity=part.stock_quantity,
        )

    async def decrement_stock(self, part_id: int, quantity: int) -> None:
        # Mutação na mesma sessão; o commit é realizado pelo repositório da OS,
        # garantindo que baixa de estoque e criação da OS sejam atômicas.
        result = await self._db.execute(select(Part).where(Part.id == part_id))
        part = result.scalar_one_or_none()
        if part is not None:
            part.stock_quantity -= quantity

    async def increment_stock(self, part_id: int, quantity: int) -> None:
        # Devolve peças ao estoque (ex.: orçamento recusado). Commit feito pelo repositório da OS.
        result = await self._db.execute(select(Part).where(Part.id == part_id))
        part = result.scalar_one_or_none()
        if part is not None:
            part.stock_quantity += quantity
