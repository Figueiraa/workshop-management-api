from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.vehicle_dtos import CreateVehicleInput, UpdateVehicleInput
from app.application.use_cases.vehicle import (
    CreateVehicleUseCase,
    DeleteVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesByClientUseCase,
    ListVehiclesUseCase,
    UpdateVehicleUseCase,
)
from app.infrastructure.database import get_db
from app.infrastructure.persistence.repositories.client_repository import SqlAlchemyClientRepository
from app.infrastructure.persistence.repositories.vehicle_repository import SqlAlchemyVehicleRepository
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.vehicle_schema import VehicleCreate, VehicleResponse, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["Veículos"])


def _repository(db: AsyncSession) -> SqlAlchemyVehicleRepository:
    return SqlAlchemyVehicleRepository(db)


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ListVehiclesUseCase(_repository(db)).execute()


@router.get("/client/{client_id}", response_model=list[VehicleResponse])
async def list_vehicles_by_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = ListVehiclesByClientUseCase(_repository(db), SqlAlchemyClientRepository(db))
    return await use_case.execute(client_id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await GetVehicleUseCase(_repository(db)).execute(vehicle_id)


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = CreateVehicleUseCase(_repository(db), SqlAlchemyClientRepository(db))
    return await use_case.execute(CreateVehicleInput(**data.model_dump()))


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = UpdateVehicleUseCase(_repository(db))
    return await use_case.execute(vehicle_id, UpdateVehicleInput(**data.model_dump()))


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    await DeleteVehicleUseCase(_repository(db)).execute(vehicle_id)
