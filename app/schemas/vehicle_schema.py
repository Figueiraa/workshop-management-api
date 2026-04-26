import re
from datetime import datetime

from pydantic import BaseModel, field_validator

# Accepts old format (ABC-1234) and Mercosul (ABC1D23)
_PLATE_RE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    client_id: int

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        normalized = v.upper().replace("-", "").strip()
        old_format = re.match(r"^[A-Z]{3}[0-9]{4}$", normalized)
        mercosul = _PLATE_RE.match(normalized)
        if not old_format and not mercosul:
            raise ValueError("Placa inválida. Use o formato ABC1234 ou ABC1D23")
        return normalized

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 1886 or v > 2100:
            raise ValueError("Ano do veículo inválido")
        return v


class VehicleUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None


class VehicleResponse(BaseModel):
    id: int
    plate: str
    brand: str
    model: str
    year: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
