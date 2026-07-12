from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.service_order_dtos import OpenServiceOrderInput
from app.application.use_cases.approve_budget import ApproveBudgetUseCase
from app.application.use_cases.auth import AuthenticateUserUseCase
from app.application.use_cases.open_service_order import OpenServiceOrderUseCase
from app.domain.entities.client import Client
from app.domain.entities.service_order import ServiceOrder
from app.domain.exceptions.domain_exceptions import NotFoundError, UnauthorizedError
from app.domain.value_objects.service_order_status import ServiceOrderStatus


@pytest.mark.asyncio
async def test_approve_budget_notifies_and_moves_to_execution():
    order = ServiceOrder(
        id=1,
        number="OS1",
        vehicle_id=1,
        client_id=7,
        total_budget=100.0,
        status=ServiceOrderStatus.AGUARDANDO_APROVACAO,
    )
    repo = AsyncMock()
    repo.get_by_id.return_value = order
    repo.update.return_value = order
    parts = AsyncMock()
    clients = AsyncMock()
    clients.get_by_id.return_value = Client(id=7, name="Ana", cpf_cnpj="1", email="ana@x.com")
    notifier = AsyncMock()

    use_case = ApproveBudgetUseCase(repo, parts, clients, notifier)
    result = await use_case.execute(order_id=1, approved=True)

    assert result.status == ServiceOrderStatus.EM_EXECUCAO
    notifier.notify_status_change.assert_awaited_once_with("ana@x.com", "OS1", "EM_EXECUCAO")
    parts.increment_stock.assert_not_awaited()  # nada devolvido em aprovação


@pytest.mark.asyncio
async def test_open_service_order_vehicle_not_found():
    repo = AsyncMock()
    vehicle_gateway = AsyncMock()
    vehicle_gateway.get_by_id.return_value = None
    use_case = OpenServiceOrderUseCase(repo, vehicle_gateway, AsyncMock(), AsyncMock())

    with pytest.raises(NotFoundError):
        await use_case.execute(OpenServiceOrderInput(vehicle_id=999))
    repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_unknown_user_runs_dummy_verify():
    repo = AsyncMock()
    repo.get_by_username.return_value = None
    hasher = MagicMock()
    tokens = MagicMock()

    use_case = AuthenticateUserUseCase(repo, hasher, tokens)
    with pytest.raises(UnauthorizedError):
        await use_case.execute("ghost", "secret")

    # Guarda contra timing attack: verificação descartável executada; token nunca emitido.
    hasher.dummy_verify.assert_called_once_with("secret")
    tokens.create_access_token.assert_not_called()
