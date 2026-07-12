from app.domain.entities.service_type import ServiceType
from app.infrastructure.persistence.models.service_type_model import ServiceType as ServiceTypeModel


def to_domain(model: ServiceTypeModel) -> ServiceType:
    return ServiceType(
        id=model.id,
        name=model.name,
        description=model.description,
        price=float(model.price),
        estimated_duration_minutes=model.estimated_duration_minutes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
