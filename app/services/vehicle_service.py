from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.domain_exceptions import ConflictError, NotFoundError
from app.models.vehicle_model import Vehicle
from app.repositories.client_repository import ClientRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle_schema import VehicleCreate, VehicleUpdate


class VehicleService:
    def __init__(self, db: AsyncSession):
        self._repo = VehicleRepository(db)
        self._client_repo = ClientRepository(db)

    async def list_all(self) -> list[Vehicle]:
        return await self._repo.get_all()

    async def get_by_id(self, vehicle_id: int) -> Vehicle:
        vehicle = await self._repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", vehicle_id)
        return vehicle

    async def list_by_client(self, client_id: int) -> list[Vehicle]:
        if not await self._client_repo.get_by_id(client_id):
            raise NotFoundError("Cliente", client_id)
        return await self._repo.get_by_client(client_id)

    async def create(self, data: VehicleCreate) -> Vehicle:
        if not await self._client_repo.get_by_id(data.client_id):
            raise NotFoundError("Cliente", data.client_id)
        if await self._repo.get_by_plate(data.plate):
            raise ConflictError(f"Placa '{data.plate}' já cadastrada")
        vehicle = Vehicle(**data.model_dump())
        return await self._repo.create(vehicle)

    async def update(self, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = await self.get_by_id(vehicle_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(vehicle, field, value)
        return await self._repo.update(vehicle)

    async def delete(self, vehicle_id: int) -> None:
        vehicle = await self.get_by_id(vehicle_id)
        await self._repo.delete(vehicle)
