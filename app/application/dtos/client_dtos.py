from dataclasses import dataclass


@dataclass
class CreateClientInput:
    name: str
    cpf_cnpj: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


@dataclass
class UpdateClientInput:
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
