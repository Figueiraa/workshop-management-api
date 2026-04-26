from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part_model import Part


class PartRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_all(self) -> list[Part]:
        result = await self._db.execute(select(Part).order_by(Part.name))
        return list(result.scalars().all())

    async def get_by_id(self, part_id: int) -> Part | None:
        result = await self._db.execute(select(Part).where(Part.id == part_id))
        return result.scalar_one_or_none()

    async def create(self, part: Part) -> Part:
        self._db.add(part)
        await self._db.commit()
        await self._db.refresh(part)
        return part

    async def update(self, part: Part) -> Part:
        await self._db.commit()
        await self._db.refresh(part)
        return part

    async def delete(self, part: Part) -> None:
        await self._db.delete(part)
        await self._db.commit()
