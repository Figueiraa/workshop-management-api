from app.application.ports.client_repository import ClientRepositoryPort
from app.application.ports.gateways import PartGatewayPort
from app.application.ports.notifier import NotifierPort
from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder
from app.domain.exceptions.domain_exceptions import NotFoundError
from app.domain.value_objects.service_order_status import ServiceOrderStatus


class ApproveBudgetUseCase:
    """Recebe a aprovação/recusa externa do orçamento de uma Ordem de Serviço.

    Aprovado: a OS avança para execução.
    Recusado: a OS é encerrada como orçamento recusado e as peças reservadas
    retornam ao estoque.
    """

    def __init__(
        self,
        repository: ServiceOrderRepositoryPort,
        part_gateway: PartGatewayPort,
        client_repository: ClientRepositoryPort,
        notifier: NotifierPort,
    ):
        self._repo = repository
        self._parts = part_gateway
        self._clients = client_repository
        self._notifier = notifier

    async def execute(self, order_id: int, approved: bool) -> ServiceOrder:
        order = await self._repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Ordem de serviço", order_id)

        if approved:
            order.transition_to(ServiceOrderStatus.EM_EXECUCAO)
        else:
            order.transition_to(ServiceOrderStatus.ORCAMENTO_RECUSADO)
            for part in order.parts:
                await self._parts.increment_stock(part.part_id, part.quantity)

        updated = await self._repo.update(order)

        client = await self._clients.get_by_id(updated.client_id)
        recipient = client.email if client else None
        await self._notifier.notify_status_change(recipient, updated.number, updated.status.value)
        return updated
