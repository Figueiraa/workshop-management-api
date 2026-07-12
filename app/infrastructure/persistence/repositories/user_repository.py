from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.user_repository import UserRepositoryPort
from app.domain.entities.user import User
from app.infrastructure.persistence.mappers.user_mapper import to_domain
from app.infrastructure.persistence.models.user_model import User as UserModel


class SqlAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self._db.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        return to_domain(model)
