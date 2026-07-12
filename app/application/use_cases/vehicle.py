from app.application.dtos.vehicle_dtos import CreateVehicleInput, UpdateVehicleInput
from app.application.ports.client_repository import ClientRepositoryPort
from app.application.ports.vehicle_repository import VehicleRepositoryPort
from app.domain.entities.vehicle import Vehicle
from app.domain.exceptions.domain_exceptions import ConflictError, NotFoundError


class ListVehiclesUseCase:
    def __init__(self, repository: VehicleRepositoryPort):
        self._repo = repository

    async def execute(self) -> list[Vehicle]:
        return await self._repo.get_all()


class GetVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort):
        self._repo = repository

    async def execute(self, vehicle_id: int) -> Vehicle:
        vehicle = await self._repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", vehicle_id)
        return vehicle


class ListVehiclesByClientUseCase:
    def __init__(self, repository: VehicleRepositoryPort, client_repository: ClientRepositoryPort):
        self._repo = repository
        self._clients = client_repository

    async def execute(self, client_id: int) -> list[Vehicle]:
        if not await self._clients.get_by_id(client_id):
            raise NotFoundError("Cliente", client_id)
        return await self._repo.get_by_client(client_id)


class CreateVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort, client_repository: ClientRepositoryPort):
        self._repo = repository
        self._clients = client_repository

    async def execute(self, data: CreateVehicleInput) -> Vehicle:
        if not await self._clients.get_by_id(data.client_id):
            raise NotFoundError("Cliente", data.client_id)
        if await self._repo.get_by_plate(data.plate):
            raise ConflictError(f"Placa '{data.plate}' já cadastrada")
        vehicle = Vehicle(
            plate=data.plate,
            brand=data.brand,
            model=data.model,
            year=data.year,
            client_id=data.client_id,
        )
        return await self._repo.add(vehicle)


class UpdateVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort):
        self._repo = repository

    async def execute(self, vehicle_id: int, data: UpdateVehicleInput) -> Vehicle:
        vehicle = await self._repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", vehicle_id)
        if data.brand is not None:
            vehicle.brand = data.brand
        if data.model is not None:
            vehicle.model = data.model
        if data.year is not None:
            vehicle.year = data.year
        return await self._repo.update(vehicle)


class DeleteVehicleUseCase:
    def __init__(self, repository: VehicleRepositoryPort):
        self._repo = repository

    async def execute(self, vehicle_id: int) -> None:
        vehicle = await self._repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Veículo", vehicle_id)
        await self._repo.delete(vehicle_id)
