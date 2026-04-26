from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.exceptions.domain_exceptions import ConflictError, NotFoundError
from app.schemas.service_type_schema import ServiceTypeCreate, ServiceTypeResponse, ServiceTypeUpdate
from app.services.service_type_service import ServiceTypeService

router = APIRouter(prefix="/service-types", tags=["Serviços"])


@router.get("", response_model=list[ServiceTypeResponse])
async def list_service_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ServiceTypeService(db).list_all()


@router.get("/{service_type_id}", response_model=ServiceTypeResponse)
async def get_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await ServiceTypeService(db).get_by_id(service_type_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ServiceTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_service_type(
    data: ServiceTypeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await ServiceTypeService(db).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{service_type_id}", response_model=ServiceTypeResponse)
async def update_service_type(
    service_type_id: int,
    data: ServiceTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        return await ServiceTypeService(db).update(service_type_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        await ServiceTypeService(db).delete(service_type_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
