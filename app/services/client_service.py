from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.domain_exceptions import ConflictError, NotFoundError
from app.models.client_model import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client_schema import ClientCreate, ClientUpdate


class ClientService:
    def __init__(self, db: AsyncSession):
        self._repo = ClientRepository(db)

    async def list_all(self) -> list[Client]:
        return await self._repo.get_all()

    async def get_by_id(self, client_id: int) -> Client:
        client = await self._repo.get_by_id(client_id)
        if not client:
            raise NotFoundError("Cliente", client_id)
        return client

    async def create(self, data: ClientCreate) -> Client:
        if await self._repo.get_by_cpf_cnpj(data.cpf_cnpj):
            raise ConflictError(f"CPF/CNPJ '{data.cpf_cnpj}' já cadastrado")
        client = Client(**data.model_dump())
        return await self._repo.create(client)

    async def update(self, client_id: int, data: ClientUpdate) -> Client:
        client = await self.get_by_id(client_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(client, field, value)
        return await self._repo.update(client)

    async def delete(self, client_id: int) -> None:
        client = await self.get_by_id(client_id)
        await self._repo.delete(client)
