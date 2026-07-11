from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.client_dtos import CreateClientInput, UpdateClientInput
from app.application.use_cases.client import (
    CreateClientUseCase,
    DeleteClientUseCase,
    GetClientUseCase,
    ListClientsUseCase,
    UpdateClientUseCase,
)
from app.infrastructure.database import get_db
from app.infrastructure.persistence.repositories.client_repository import SqlAlchemyClientRepository
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clientes"])


def _repository(db: AsyncSession) -> SqlAlchemyClientRepository:
    return SqlAlchemyClientRepository(db)


@router.get("", response_model=list[ClientResponse])
async def list_clients(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await ListClientsUseCase(_repository(db)).execute()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await GetClientUseCase(_repository(db)).execute(client_id)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await CreateClientUseCase(_repository(db)).execute(CreateClientInput(**data.model_dump()))


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    use_case = UpdateClientUseCase(_repository(db))
    return await use_case.execute(client_id, UpdateClientInput(**data.model_dump()))


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    await DeleteClientUseCase(_repository(db)).execute(client_id)
