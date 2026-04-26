from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.domain_exceptions import ConflictError, NotFoundError
from app.models.service_type_model import ServiceType
from app.repositories.service_type_repository import ServiceTypeRepository
from app.schemas.service_type_schema import ServiceTypeCreate, ServiceTypeUpdate


class ServiceTypeService:
    def __init__(self, db: AsyncSession):
        self._repo = ServiceTypeRepository(db)

    async def list_all(self) -> list[ServiceType]:
        return await self._repo.get_all()

    async def get_by_id(self, service_type_id: int) -> ServiceType:
        service_type = await self._repo.get_by_id(service_type_id)
        if not service_type:
            raise NotFoundError("Serviço", service_type_id)
        return service_type

    async def create(self, data: ServiceTypeCreate) -> ServiceType:
        if await self._repo.get_by_name(data.name):
            raise ConflictError(f"Serviço '{data.name}' já cadastrado")
        service_type = ServiceType(**data.model_dump())
        return await self._repo.create(service_type)

    async def update(self, service_type_id: int, data: ServiceTypeUpdate) -> ServiceType:
        service_type = await self.get_by_id(service_type_id)
        if data.name and data.name != service_type.name:
            if await self._repo.get_by_name(data.name):
                raise ConflictError(f"Serviço '{data.name}' já cadastrado")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(service_type, field, value)
        return await self._repo.update(service_type)

    async def delete(self, service_type_id: int) -> None:
        service_type = await self.get_by_id(service_type_id)
        await self._repo.delete(service_type)
