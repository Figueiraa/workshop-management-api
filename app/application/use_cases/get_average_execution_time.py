from app.application.dtos.service_order_dtos import AverageExecutionTimeResult
from app.application.ports.service_order_repository import ServiceOrderRepositoryPort


class GetAverageExecutionTimeUseCase:
    def __init__(self, repository: ServiceOrderRepositoryPort):
        self._repo = repository

    async def execute(self) -> AverageExecutionTimeResult:
        orders = await self._repo.get_completed_with_times()
        if not orders:
            return AverageExecutionTimeResult(average_minutes=None, total_completed=0)

        total_minutes = sum(
            (order.completed_at - order.started_at).total_seconds() / 60
            for order in orders
            if order.completed_at is not None and order.started_at is not None
        )
        return AverageExecutionTimeResult(
            average_minutes=round(total_minutes / len(orders), 2),
            total_completed=len(orders),
        )
