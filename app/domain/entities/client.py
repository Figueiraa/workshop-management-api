from dataclasses import dataclass
from datetime import datetime


@dataclass
class Client:
    name: str
    cpf_cnpj: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
