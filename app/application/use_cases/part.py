from app.application.dtos.part_dtos import CreatePartInput, UpdatePartInput
from app.application.ports.part_repository import PartRepositoryPort
from app.domain.entities.part import Part
from app.domain.exceptions.domain_exceptions import NotFoundError


class ListPartsUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self) -> list[Part]:
        return await self._repo.get_all()


class GetPartUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self, part_id: int) -> Part:
        part = await self._repo.get_by_id(part_id)
        if not part:
            raise NotFoundError("Peça/Insumo", part_id)
        return part


class CreatePartUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self, data: CreatePartInput) -> Part:
        part = Part(
            name=data.name,
            unit_price=data.unit_price,
            stock_quantity=data.stock_quantity,
            unit=data.unit,
            description=data.description,
        )
        return await self._repo.add(part)


class UpdatePartUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self, part_id: int, data: UpdatePartInput) -> Part:
        part = await self._repo.get_by_id(part_id)
        if not part:
            raise NotFoundError("Peça/Insumo", part_id)
        if data.name is not None:
            part.name = data.name
        if data.description is not None:
            part.description = data.description
        if data.unit_price is not None:
            part.unit_price = data.unit_price
        if data.unit is not None:
            part.unit = data.unit
        return await self._repo.update(part)


class AdjustPartStockUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self, part_id: int, quantity: int) -> Part:
        part = await self._repo.get_by_id(part_id)
        if not part:
            raise NotFoundError("Peça/Insumo", part_id)
        part.adjust_stock(quantity)  # regra de negócio na entidade
        return await self._repo.update(part)


class DeletePartUseCase:
    def __init__(self, repository: PartRepositoryPort):
        self._repo = repository

    async def execute(self, part_id: int) -> None:
        part = await self._repo.get_by_id(part_id)
        if not part:
            raise NotFoundError("Peça/Insumo", part_id)
        await self._repo.delete(part_id)
