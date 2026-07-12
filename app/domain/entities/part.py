from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions.domain_exceptions import BusinessRuleError


@dataclass
class Part:
    name: str
    unit_price: float
    stock_quantity: int = 0
    unit: str = "un"
    description: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def adjust_stock(self, quantity: int) -> None:
        """Ajusta o estoque (positivo ou negativo), impedindo saldo negativo."""
        new_quantity = self.stock_quantity + quantity
        if new_quantity < 0:
            raise BusinessRuleError(
                f"Estoque insuficiente: disponível {self.stock_quantity}, ajuste solicitado {quantity}"
            )
        self.stock_quantity = new_quantity
