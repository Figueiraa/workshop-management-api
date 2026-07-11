from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.application.ports.security import PasswordHasherPort, TokenIssuerPort
from app.infrastructure.config import settings

_password_hash = PasswordHash.recommended()

# Hash descartável usado para manter tempo de resposta constante quando o usuário não existe,
# impedindo enumeração de usuários por latência.
_DUMMY_HASH = _password_hash.hash("dummy-password-for-constant-time")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except InvalidTokenError:
        return None


class PasswordHasher(PasswordHasherPort):
    """Adapter de hashing (Argon2 via pwdlib) que implementa a port de aplicação."""

    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)

    def dummy_verify(self, plain: str) -> None:
        verify_password(plain, _DUMMY_HASH)


class TokenIssuer(TokenIssuerPort):
    """Adapter de emissão de token (JWT via PyJWT) que implementa a port de aplicação."""

    def create_access_token(self, subject: str) -> str:
        return create_access_token(subject)
