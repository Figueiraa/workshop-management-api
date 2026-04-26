from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_type_model import ServiceType


class ServiceTypeRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_all(self) -> list[ServiceType]:
        result = await self._db.execute(select(ServiceType).order_by(ServiceType.name))
        return list(result.scalars().all())

    async def get_by_id(self, service_type_id: int) -> ServiceType | None:
        result = await self._db.execute(select(ServiceType).where(ServiceType.id == service_type_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> ServiceType | None:
        result = await self._db.execute(select(ServiceType).where(ServiceType.name == name))
        return result.scalar_one_or_none()

    async def create(self, service_type: ServiceType) -> ServiceType:
        self._db.add(service_type)
        await self._db.commit()
        await self._db.refresh(service_type)
        return service_type

    async def update(self, service_type: ServiceType) -> ServiceType:
        await self._db.commit()
        await self._db.refresh(service_type)
        return service_type

    async def delete(self, service_type: ServiceType) -> None:
        await self._db.delete(service_type)
        await self._db.commit()
