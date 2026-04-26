from datetime import datetime

from pydantic import BaseModel


class ServiceTypeCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    estimated_duration_minutes: int = 60


class ServiceTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    estimated_duration_minutes: int | None = None


class ServiceTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    estimated_duration_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
