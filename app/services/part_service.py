from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.domain_exceptions import BusinessRuleError, NotFoundError
from app.models.part_model import Part
from app.repositories.part_repository import PartRepository
from app.schemas.part_schema import PartCreate, PartUpdate


class PartService:
    def __init__(self, db: AsyncSession):
        self._repo = PartRepository(db)

    async def list_all(self) -> list[Part]:
        return await self._repo.get_all()

    async def get_by_id(self, part_id: int) -> Part:
        part = await self._repo.get_by_id(part_id)
        if not part:
            raise NotFoundError("Peça/Insumo", part_id)
        return part

    async def create(self, data: PartCreate) -> Part:
        part = Part(**data.model_dump())
        return await self._repo.create(part)

    async def update(self, part_id: int, data: PartUpdate) -> Part:
        part = await self.get_by_id(part_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(part, field, value)
        return await self._repo.update(part)

    async def adjust_stock(self, part_id: int, quantity: int) -> Part:
        part = await self.get_by_id(part_id)
        new_qty = part.stock_quantity + quantity
        if new_qty < 0:
            raise BusinessRuleError(
                f"Estoque insuficiente: disponível {part.stock_quantity}, ajuste solicitado {quantity}"
            )
        part.stock_quantity = new_qty
        return await self._repo.update(part)

    async def delete(self, part_id: int) -> None:
        part = await self.get_by_id(part_id)
        await self._repo.delete(part)
