from typing import Protocol


class NotifierPort(Protocol):
    """Contrato de notificação de mudança de status da Ordem de Serviço."""

    async def notify_status_change(
        self, recipient: str | None, order_number: str, new_status: str
    ) -> None: ...
