# Shim de compatibilidade — as exceções de domínio foram movidas para a camada de domínio
# (app/domain/exceptions) na migração para Clean Architecture. Este módulo será removido
# quando todos os imports forem atualizados para o novo caminho.
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleError,
    ConflictError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    NotFoundError,
)

__all__ = [
    "BusinessRuleError",
    "ConflictError",
    "InsufficientStockError",
    "InvalidStatusTransitionError",
    "NotFoundError",
]
