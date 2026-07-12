from app.domain.entities.part import Part
from app.infrastructure.persistence.models.part_model import Part as PartModel


def to_domain(model: PartModel) -> Part:
    return Part(
        id=model.id,
        name=model.name,
        description=model.description,
        unit_price=float(model.unit_price),
        stock_quantity=model.stock_quantity,
        unit=model.unit,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
