from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle_model import Vehicle


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_all(self) -> list[Vehicle]:
        result = await self._db.execute(select(Vehicle).order_by(Vehicle.plate))
        return list(result.scalars().all())

    async def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        result = await self._db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
        return result.scalar_one_or_none()

    async def get_by_plate(self, plate: str) -> Vehicle | None:
        result = await self._db.execute(select(Vehicle).where(Vehicle.plate == plate))
        return result.scalar_one_or_none()

    async def get_by_client(self, client_id: int) -> list[Vehicle]:
        result = await self._db.execute(select(Vehicle).where(Vehicle.client_id == client_id))
        return list(result.scalars().all())

    async def create(self, vehicle: Vehicle) -> Vehicle:
        self._db.add(vehicle)
        await self._db.commit()
        await self._db.refresh(vehicle)
        return vehicle

    async def update(self, vehicle: Vehicle) -> Vehicle:
        await self._db.commit()
        await self._db.refresh(vehicle)
        return vehicle

    async def delete(self, vehicle: Vehicle) -> None:
        await self._db.delete(vehicle)
        await self._db.commit()
