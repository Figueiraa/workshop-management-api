from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.part_repository import PartRepositoryPort
from app.domain.entities.part import Part
from app.infrastructure.persistence.mappers.part_mapper import to_domain
from app.infrastructure.persistence.models.part_model import Part as PartModel


class SqlAlchemyPartRepository(PartRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_model(self, part_id: int) -> PartModel | None:
        result = await self._db.execute(select(PartModel).where(PartModel.id == part_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Part]:
        result = await self._db.execute(select(PartModel).order_by(PartModel.name))
        return [to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, part_id: int) -> Part | None:
        model = await self._get_model(part_id)
        return to_domain(model) if model else None

    async def add(self, part: Part) -> Part:
        model = PartModel(
            name=part.name,
            description=part.description,
            unit_price=part.unit_price,
            stock_quantity=part.stock_quantity,
            unit=part.unit,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def update(self, part: Part) -> Part:
        model = await self._get_model(part.id)
        model.name = part.name
        model.description = part.description
        model.unit_price = part.unit_price
        model.stock_quantity = part.stock_quantity
        model.unit = part.unit
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)

    async def delete(self, part_id: int) -> None:
        model = await self._get_model(part_id)
        if model is not None:
            await self._db.delete(model)
            await self._db.commit()
