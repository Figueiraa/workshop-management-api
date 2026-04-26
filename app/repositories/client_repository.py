from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_model import Client


class ClientRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_all(self) -> list[Client]:
        result = await self._db.execute(select(Client).order_by(Client.name))
        return list(result.scalars().all())

    async def get_by_id(self, client_id: int) -> Client | None:
        result = await self._db.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()

    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Client | None:
        result = await self._db.execute(select(Client).where(Client.cpf_cnpj == cpf_cnpj))
        return result.scalar_one_or_none()

    async def create(self, client: Client) -> Client:
        self._db.add(client)
        await self._db.commit()
        await self._db.refresh(client)
        return client

    async def update(self, client: Client) -> Client:
        await self._db.commit()
        await self._db.refresh(client)
        return client

    async def delete(self, client: Client) -> None:
        await self._db.delete(client)
        await self._db.commit()
