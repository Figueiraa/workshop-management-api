from dataclasses import dataclass


@dataclass
class CreateVehicleInput:
    plate: str
    brand: str
    model: str
    year: int
    client_id: int


@dataclass
class UpdateVehicleInput:
    brand: str | None = None
    model: str | None = None
    year: int | None = None
