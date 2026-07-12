from dataclasses import dataclass
from datetime import datetime


@dataclass
class Vehicle:
    plate: str
    brand: str
    model: str
    year: int
    client_id: int
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
