from datetime import datetime

from pydantic import BaseModel


class PartCreate(BaseModel):
    name: str
    description: str | None = None
    unit_price: float
    stock_quantity: int = 0
    unit: str = "un"


class PartUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit_price: float | None = None
    unit: str | None = None


class StockAdjust(BaseModel):
    quantity: int


class PartResponse(BaseModel):
    id: int
    name: str
    description: str | None
    unit_price: float
    stock_quantity: int
    unit: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
