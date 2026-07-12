from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.service_type_repository import ServiceTypeRepositoryPort
from app.domain.entities.service_type import ServiceType
from app.infrastructure.persistence.mappers.service_type_mapper import to_domain
from app.infrastructure.persistence.models.service_type_model import ServiceType as ServiceTypeModel


class SqlAlchemyServiceTypeRepository(ServiceTypeRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_model(self, service_type_id: int) -> ServiceTypeModel | None:
        result = await self._db.execute(
            select(ServiceTypeModel).where(ServiceTypeModel.id == service_type_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ServiceType]:
        result = await self._db.execute(select(ServiceTypeModel).order_by(ServiceTypeModel.name))
        return [to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, service_type_id: int) -> ServiceType | None:
        model = await self._get_model(service_type_id)
        return to_domain(model) if model else None

    async def get_by_name(self, name: str) -> ServiceType | None:
        result = await self._db.execute(select(ServiceTypeModel).where(ServiceTypeModel.name == name))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, service_type: ServiceType) -> ServiceType:
        model = ServiceTypeModel(
            name=service_type.name,
            description=service_type.description,
            price=service_type.price,
            estimated_duration_minutes=service_type.estimated_duration_minutes,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def update(self, service_type: ServiceType) -> ServiceType:
        model = await self._get_model(service_type.id)
        model.name = service_type.name
        model.description = service_type.description
        model.price = service_type.price
        model.estimated_duration_minutes = service_type.estimated_duration_minutes
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def delete(self, service_type_id: int) -> None:
        model = await self._get_model(service_type_id)
        if model is not None:
            await self._db.delete(model)
            await self._db.commit()
