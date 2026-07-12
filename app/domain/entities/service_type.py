from dataclasses import dataclass
from datetime import datetime


@dataclass
class ServiceType:
    name: str
    price: float
    estimated_duration_minutes: int = 60
    description: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
