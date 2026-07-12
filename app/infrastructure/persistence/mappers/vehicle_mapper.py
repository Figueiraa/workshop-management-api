from app.domain.entities.vehicle import Vehicle
from app.infrastructure.persistence.models.vehicle_model import Vehicle as VehicleModel


def to_domain(model: VehicleModel) -> Vehicle:
    return Vehicle(
        id=model.id,
        plate=model.plate,
        brand=model.brand,
        model=model.model,
        year=model.year,
        client_id=model.client_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
