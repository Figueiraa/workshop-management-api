from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder
from app.domain.exceptions.domain_exceptions import NotFoundError


class GetServiceOrderUseCase:
    def __init__(self, repository: ServiceOrderRepositoryPort):
        self._repo = repository

    async def execute(self, order_id: int) -> ServiceOrder:
        order = await self._repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Ordem de serviço", order_id)
        return order
