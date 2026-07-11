from typing import Protocol


class PasswordHasherPort(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...

    def dummy_verify(self, plain: str) -> None:
        """Executa uma verificação descartável (contra timing attack / enumeração de usuários)."""
        ...


class TokenIssuerPort(Protocol):
    def create_access_token(self, subject: str) -> str: ...
