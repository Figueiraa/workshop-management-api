from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.client_repository import ClientRepositoryPort
from app.domain.entities.client import Client
from app.infrastructure.persistence.mappers.client_mapper import to_domain
from app.infrastructure.persistence.models.client_model import Client as ClientModel


class SqlAlchemyClientRepository(ClientRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_model(self, client_id: int) -> ClientModel | None:
        result = await self._db.execute(select(ClientModel).where(ClientModel.id == client_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Client]:
        result = await self._db.execute(select(ClientModel).order_by(ClientModel.name))
        return [to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, client_id: int) -> Client | None:
        model = await self._get_model(client_id)
        return to_domain(model) if model else None

    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Client | None:
        result = await self._db.execute(select(ClientModel).where(ClientModel.cpf_cnpj == cpf_cnpj))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, client: Client) -> Client:
        model = ClientModel(
            name=client.name,
            cpf_cnpj=client.cpf_cnpj,
            phone=client.phone,
            email=client.email,
            address=client.address,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def update(self, client: Client) -> Client:
        model = await self._get_model(client.id)
        model.name = client.name
        model.phone = client.phone
        model.email = client.email
        model.address = client.address
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def delete(self, client_id: int) -> None:
        model = await self._get_model(client_id)
        if model is not None:
            await self._db.delete(model)
            await self._db.commit()
