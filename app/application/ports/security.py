from typing import Protocol


class PasswordHasherPort(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenIssuerPort(Protocol):
    def create_access_token(self, subject: str) -> str: ...
