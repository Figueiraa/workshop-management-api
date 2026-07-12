from app.domain.entities.service_order import ServiceOrder, ServiceOrderItem, ServiceOrderPart
from app.infrastructure.persistence.models.service_order_model import ServiceOrder as ServiceOrderModel
from app.infrastructure.persistence.models.service_order_model import (
    ServiceOrderItem as ServiceOrderItemModel,
)
from app.infrastructure.persistence.models.service_order_model import (
    ServiceOrderPart as ServiceOrderPartModel,
)


def to_domain(model: ServiceOrderModel) -> ServiceOrder:
    """Converte o modelo ORM na entidade de domínio pura."""
    return ServiceOrder(
        id=model.id,
        number=model.number,
        vehicle_id=model.vehicle_id,
        client_id=model.client_id,
        status=model.status,
        notes=model.notes,
        total_budget=float(model.total_budget),
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        delivered_at=model.delivered_at,
        items=[
            ServiceOrderItem(
                id=item.id,
                service_type_id=item.service_type_id,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
            )
            for item in model.items
        ],
        parts=[
            ServiceOrderPart(
                id=part.id,
                part_id=part.part_id,
                quantity=part.quantity,
                unit_price=float(part.unit_price),
            )
            for part in model.parts
        ],
    )


def to_model(entity: ServiceOrder) -> ServiceOrderModel:
    """Cria um novo modelo ORM a partir da entidade de domínio (para inserção)."""
    return ServiceOrderModel(
        number=entity.number,
        vehicle_id=entity.vehicle_id,
        client_id=entity.client_id,
        status=entity.status,
        notes=entity.notes,
        total_budget=entity.total_budget,
        items=[
            ServiceOrderItemModel(
                service_type_id=item.service_type_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in entity.items
        ],
        parts=[
            ServiceOrderPartModel(
                part_id=part.part_id,
                quantity=part.quantity,
                unit_price=part.unit_price,
            )
            for part in entity.parts
        ],
    )
