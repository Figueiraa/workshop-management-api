from datetime import datetime

from pydantic import BaseModel

from app.models.service_order_model import ServiceOrderStatus


class ServiceOrderItemInput(BaseModel):
    service_type_id: int
    quantity: int = 1


class ServiceOrderPartInput(BaseModel):
    part_id: int
    quantity: int = 1


class ServiceOrderCreate(BaseModel):
    vehicle_id: int
    notes: str | None = None
    items: list[ServiceOrderItemInput] = []
    parts: list[ServiceOrderPartInput] = []


class ServiceOrderUpdateStatus(BaseModel):
    status: ServiceOrderStatus


class ServiceOrderItemResponse(BaseModel):
    id: int
    service_type_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class ServiceOrderPartResponse(BaseModel):
    id: int
    part_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class ServiceOrderResponse(BaseModel):
    id: int
    number: str
    vehicle_id: int
    client_id: int
    status: ServiceOrderStatus
    notes: str | None
    total_budget: float
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    items: list[ServiceOrderItemResponse]
    parts: list[ServiceOrderPartResponse]

    model_config = {"from_attributes": True}


class ServiceOrderSummary(BaseModel):
    id: int
    number: str
    vehicle_id: int
    client_id: int
    status: ServiceOrderStatus
    total_budget: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AverageExecutionTimeResponse(BaseModel):
    average_minutes: float | None
    total_completed: int
