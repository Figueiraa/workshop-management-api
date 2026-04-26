from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.exceptions.domain_exceptions import BusinessRuleError, NotFoundError
from app.schemas.part_schema import PartCreate, PartResponse, PartUpdate, StockAdjust
from app.services.part_service import PartService

router = APIRouter(prefix="/parts", tags=["Peças e Insumos"])


@router.get("", response_model=list[PartResponse])
async def list_parts(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await PartService(db).list_all()


@router.get("/{part_id}", response_model=PartResponse)
async def get_part(part_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    try:
        return await PartService(db).get_by_id(part_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
async def create_part(data: PartCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await PartService(db).create(data)


@router.patch("/{part_id}", response_model=PartResponse)
async def update_part(
    part_id: int,
    data: PartUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await PartService(db).update(part_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{part_id}/stock", response_model=PartResponse)
async def adjust_stock(
    part_id: int,
    data: StockAdjust,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await PartService(db).adjust_stock(part_id, data.quantity)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(part_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    try:
        await PartService(db).delete(part_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
