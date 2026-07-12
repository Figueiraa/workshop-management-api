from app.application.ports.client_repository import ClientRepositoryPort
from app.application.ports.notifier import NotifierPort
from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder
from app.domain.exceptions.domain_exceptions import NotFoundError
from app.domain.value_objects.service_order_status import ServiceOrderStatus


class UpdateServiceOrderStatusUseCase:
    def __init__(
        self,
        repository: ServiceOrderRepositoryPort,
        client_repository: ClientRepositoryPort,
        notifier: NotifierPort,
    ):
        self._repo = repository
        self._clients = client_repository
        self._notifier = notifier

    async def execute(self, order_id: int, new_status: ServiceOrderStatus) -> ServiceOrder:
        order = await self._repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Ordem de serviço", order_id)
        # A regra de transição (validação + timestamps) vive na entidade de domínio.
        order.transition_to(new_status)
        updated = await self._repo.update(order)

        client = await self._clients.get_by_id(updated.client_id)
        recipient = client.email if client else None
        await self._notifier.notify_status_change(recipient, updated.number, updated.status.value)
        return updated
