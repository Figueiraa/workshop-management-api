from dataclasses import dataclass
from typing import Protocol


@dataclass
class VehicleRef:
    id: int
    client_id: int


@dataclass
class ServiceTypeRef:
    id: int
    price: float


@dataclass
class PartRef:
    id: int
    name: str
    unit_price: float
    stock_quantity: int


class VehicleGatewayPort(Protocol):
    async def get_by_id(self, vehicle_id: int) -> VehicleRef | None: ...


class ServiceTypeGatewayPort(Protocol):
    async def get_by_id(self, service_type_id: int) -> ServiceTypeRef | None: ...


class PartGatewayPort(Protocol):
    async def get_by_id(self, part_id: int) -> PartRef | None: ...

    async def decrement_stock(self, part_id: int, quantity: int) -> None: ...
