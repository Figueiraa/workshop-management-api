from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.service_type_dtos import CreateServiceTypeInput, UpdateServiceTypeInput
from app.application.use_cases.service_type import (
    CreateServiceTypeUseCase,
    DeleteServiceTypeUseCase,
    GetServiceTypeUseCase,
    ListServiceTypesUseCase,
    UpdateServiceTypeUseCase,
)
from app.infrastructure.database import get_db
from app.infrastructure.persistence.repositories.service_type_repository import (
    SqlAlchemyServiceTypeRepository,
)
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.service_type_schema import (
    ServiceTypeCreate,
    ServiceTypeResponse,
    ServiceTypeUpdate,
)

router = APIRouter(prefix="/service-types", tags=["Serviços"])


def _repository(db: AsyncSession) -> SqlAlchemyServiceTypeRepository:
    return SqlAlchemyServiceTypeRepository(db)


@router.get("", response_model=list[ServiceTypeResponse])
async def list_service_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ListServiceTypesUseCase(_repository(db)).execute()


@router.get("/{service_type_id}", response_model=ServiceTypeResponse)
async def get_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await GetServiceTypeUseCase(_repository(db)).execute(service_type_id)


@router.post("", response_model=ServiceTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_service_type(
    data: ServiceTypeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = CreateServiceTypeUseCase(_repository(db))
    return await use_case.execute(CreateServiceTypeInput(**data.model_dump()))


@router.patch("/{service_type_id}", response_model=ServiceTypeResponse)
async def update_service_type(
    service_type_id: int,
    data: ServiceTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = UpdateServiceTypeUseCase(_repository(db))
    payload = UpdateServiceTypeInput(**data.model_dump())
    return await use_case.execute(service_type_id, payload)


@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await DeleteServiceTypeUseCase(_repository(db)).execute(service_type_id)
