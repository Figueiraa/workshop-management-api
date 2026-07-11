from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.part_dtos import CreatePartInput, UpdatePartInput
from app.application.use_cases.part import (
    AdjustPartStockUseCase,
    CreatePartUseCase,
    DeletePartUseCase,
    GetPartUseCase,
    ListPartsUseCase,
    UpdatePartUseCase,
)
from app.infrastructure.database import get_db
from app.infrastructure.persistence.repositories.part_repository import SqlAlchemyPartRepository
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.part_schema import PartCreate, PartResponse, PartUpdate, StockAdjust

router = APIRouter(prefix="/parts", tags=["Peças e Insumos"])


def _repository(db: AsyncSession) -> SqlAlchemyPartRepository:
    return SqlAlchemyPartRepository(db)


@router.get("", response_model=list[PartResponse])
async def list_parts(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ListPartsUseCase(_repository(db)).execute()


@router.get("/{part_id}", response_model=PartResponse)
async def get_part(part_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await GetPartUseCase(_repository(db)).execute(part_id)


@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
async def create_part(data: PartCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await CreatePartUseCase(_repository(db)).execute(CreatePartInput(**data.model_dump()))


@router.patch("/{part_id}", response_model=PartResponse)
async def update_part(
    part_id: int,
    data: PartUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await UpdatePartUseCase(_repository(db)).execute(part_id, UpdatePartInput(**data.model_dump()))


@router.post("/{part_id}/stock", response_model=PartResponse)
async def adjust_stock(
    part_id: int,
    data: StockAdjust,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await AdjustPartStockUseCase(_repository(db)).execute(part_id, data.quantity)


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(part_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    await DeletePartUseCase(_repository(db)).execute(part_id)
