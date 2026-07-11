from app.application.dtos.auth_dtos import RegisterUserInput
from app.application.ports.security import PasswordHasherPort, TokenIssuerPort
from app.application.ports.user_repository import UserRepositoryPort
from app.domain.entities.user import User
from app.domain.exceptions.domain_exceptions import ConflictError, UnauthorizedError


class RegisterUserUseCase:
    def __init__(self, repository: UserRepositoryPort, hasher: PasswordHasherPort):
        self._repo = repository
        self._hasher = hasher

    async def execute(self, data: RegisterUserInput) -> User:
        if await self._repo.get_by_username(data.username):
            raise ConflictError(f"Username '{data.username}' já está em uso")
        if await self._repo.get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' já está cadastrado")
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self._hasher.hash(data.password),
        )
        return await self._repo.add(user)


class AuthenticateUserUseCase:
    def __init__(
        self,
        repository: UserRepositoryPort,
        hasher: PasswordHasherPort,
        token_issuer: TokenIssuerPort,
    ):
        self._repo = repository
        self._hasher = hasher
        self._tokens = token_issuer

    async def execute(self, username: str, password: str) -> str:
        user = await self._repo.get_by_username(username)
        if not user or not self._hasher.verify(password, user.password_hash):
            raise UnauthorizedError()
        if not user.is_active:
            raise UnauthorizedError()
        return self._tokens.create_access_token(user.username)
