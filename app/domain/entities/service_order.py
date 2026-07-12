from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.exceptions.domain_exceptions import InvalidStatusTransitionError
from app.domain.value_objects.service_order_status import VALID_TRANSITIONS, ServiceOrderStatus


@dataclass
class ServiceOrderItem:
    """Serviço aplicado a uma Ordem de Serviço."""

    service_type_id: int
    quantity: int
    unit_price: float
    id: int | None = None


@dataclass
class ServiceOrderPart:
    """Peça/insumo consumido em uma Ordem de Serviço."""

    part_id: int
    quantity: int
    unit_price: float
    id: int | None = None


@dataclass
class ServiceOrder:
    """Entidade de domínio da Ordem de Serviço (Python puro, sem ORM)."""

    number: str
    vehicle_id: int
    client_id: int
    total_budget: float
    status: ServiceOrderStatus = ServiceOrderStatus.RECEBIDA
    notes: str | None = None
    items: list[ServiceOrderItem] = field(default_factory=list)
    parts: list[ServiceOrderPart] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    delivered_at: datetime | None = None

    def transition_to(self, new_status: ServiceOrderStatus, now: datetime | None = None) -> None:
        """Transiciona o status respeitando a máquina de estados do domínio.

        Registra o instante das transições relevantes (início, conclusão, entrega).
        Levanta ``InvalidStatusTransitionError`` se a transição não for permitida.
        """
        if new_status not in VALID_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(self.status.value, new_status.value)

        moment = now or datetime.now(UTC)
        if new_status == ServiceOrderStatus.EM_EXECUCAO:
            self.started_at = moment
        elif new_status == ServiceOrderStatus.FINALIZADA:
            self.completed_at = moment
        elif new_status == ServiceOrderStatus.ENTREGUE:
            self.delivered_at = moment

        self.status = new_status
