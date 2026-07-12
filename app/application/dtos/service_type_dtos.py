from dataclasses import dataclass


@dataclass
class CreateServiceTypeInput:
    name: str
    price: float
    estimated_duration_minutes: int = 60
    description: str | None = None


@dataclass
class UpdateServiceTypeInput:
    name: str | None = None
    description: str | None = None
    price: float | None = None
    estimated_duration_minutes: int | None = None
