class NotFoundError(Exception):
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' não encontrado")


class ConflictError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class BusinessRuleError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class InsufficientStockError(Exception):
    def __init__(self, part_name: str, available: int, requested: int):
        super().__init__(
            f"Estoque insuficiente para '{part_name}': disponível {available}, solicitado {requested}"
        )


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Transição de status inválida: '{current}' → '{target}'")


class UnauthorizedError(Exception):
    def __init__(self, message: str = "Credenciais inválidas"):
        super().__init__(message)
