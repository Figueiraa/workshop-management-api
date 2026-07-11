from dataclasses import dataclass


@dataclass
class CreatePartInput:
    name: str
    unit_price: float
    stock_quantity: int = 0
    unit: str = "un"
    description: str | None = None


@dataclass
class UpdatePartInput:
    name: str | None = None
    description: str | None = None
    unit_price: float | None = None
    unit: str | None = None
