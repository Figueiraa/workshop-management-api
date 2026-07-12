from app.application.ports.service_order_repository import ServiceOrderRepositoryPort
from app.domain.entities.service_order import ServiceOrder
from app.domain.value_objects.service_order_status import ServiceOrderStatus


class ListServiceOrdersUseCase:
    def __init__(self, repository: ServiceOrderRepositoryPort):
        self._repo = repository

    async def execute(self, status: ServiceOrderStatus | None = None) -> list[ServiceOrder]:
        if status is not None:
            return await self._repo.get_by_status(status)
        # Sem filtro: lista apenas OS ativas, ordenadas por prioridade de status.
        return await self._repo.list_open_ordered()
