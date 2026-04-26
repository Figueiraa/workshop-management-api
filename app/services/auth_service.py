from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.domain_exceptions import ConflictError, NotFoundError
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self._repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        if await self._repo.get_by_username(data.username):
            raise ConflictError(f"Username '{data.username}' já está em uso")
        if await self._repo.get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' já está cadastrado")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        return await self._repo.create(user)

    async def login(self, username: str, password: str) -> str:
        user = await self._repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise NotFoundError("Credenciais", "inválidas")
        if not user.is_active:
            raise NotFoundError("Usuário", username)
        return create_access_token(user.username)
