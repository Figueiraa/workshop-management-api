from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.vehicle_repository import VehicleRepositoryPort
from app.domain.entities.vehicle import Vehicle
from app.infrastructure.persistence.mappers.vehicle_mapper import to_domain
from app.infrastructure.persistence.models.vehicle_model import Vehicle as VehicleModel


class SqlAlchemyVehicleRepository(VehicleRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_model(self, vehicle_id: int) -> VehicleModel | None:
        result = await self._db.execute(select(VehicleModel).where(VehicleModel.id == vehicle_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Vehicle]:
        result = await self._db.execute(select(VehicleModel).order_by(VehicleModel.plate))
        return [to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        model = await self._get_model(vehicle_id)
        return to_domain(model) if model else None

    async def get_by_plate(self, plate: str) -> Vehicle | None:
        result = await self._db.execute(select(VehicleModel).where(VehicleModel.plate == plate))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_client(self, client_id: int) -> list[Vehicle]:
        result = await self._db.execute(select(VehicleModel).where(VehicleModel.client_id == client_id))
        return [to_domain(model) for model in result.scalars().all()]

    async def add(self, vehicle: Vehicle) -> Vehicle:
        model = VehicleModel(
            plate=vehicle.plate,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year,
            client_id=vehicle.client_id,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def update(self, vehicle: Vehicle) -> Vehicle:
        model = await self._get_model(vehicle.id)
        model.brand = vehicle.brand
        model.model = vehicle.model
        model.year = vehicle.year
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def delete(self, vehicle_id: int) -> None:
        model = await self._get_model(vehicle_id)
        if model is not None:
            await self._db.delete(model)
            await self._db.commit()
