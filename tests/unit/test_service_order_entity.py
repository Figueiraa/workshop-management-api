from datetime import UTC, datetime

import pytest

from app.domain.entities.service_order import ServiceOrder
from app.domain.exceptions.domain_exceptions import InvalidStatusTransitionError
from app.domain.value_objects.service_order_status import ServiceOrderStatus


def _order(status: ServiceOrderStatus) -> ServiceOrder:
    return ServiceOrder(
        number="OS202607110001",
        vehicle_id=1,
        client_id=1,
        total_budget=100.0,
        status=status,
    )


def test_valid_transition_updates_status():
    order = _order(ServiceOrderStatus.RECEBIDA)
    order.transition_to(ServiceOrderStatus.EM_DIAGNOSTICO)
    assert order.status == ServiceOrderStatus.EM_DIAGNOSTICO


def test_invalid_transition_raises():
    order = _order(ServiceOrderStatus.RECEBIDA)
    with pytest.raises(InvalidStatusTransitionError):
        order.transition_to(ServiceOrderStatus.ENTREGUE)


def test_terminal_status_has_no_transitions():
    order = _order(ServiceOrderStatus.ENTREGUE)
    with pytest.raises(InvalidStatusTransitionError):
        order.transition_to(ServiceOrderStatus.RECEBIDA)


def test_transition_to_execution_sets_started_at():
    order = _order(ServiceOrderStatus.AGUARDANDO_APROVACAO)
    moment = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    order.transition_to(ServiceOrderStatus.EM_EXECUCAO, now=moment)
    assert order.started_at == moment
    assert order.completed_at is None


def test_transition_to_finalized_sets_completed_at():
    order = _order(ServiceOrderStatus.EM_EXECUCAO)
    moment = datetime(2026, 7, 11, 13, 0, tzinfo=UTC)
    order.transition_to(ServiceOrderStatus.FINALIZADA, now=moment)
    assert order.completed_at == moment


def test_transition_to_delivered_sets_delivered_at():
    order = _order(ServiceOrderStatus.FINALIZADA)
    moment = datetime(2026, 7, 11, 14, 0, tzinfo=UTC)
    order.transition_to(ServiceOrderStatus.ENTREGUE, now=moment)
    assert order.delivered_at == moment


def test_full_happy_path():
    order = _order(ServiceOrderStatus.RECEBIDA)
    for target in (
        ServiceOrderStatus.EM_DIAGNOSTICO,
        ServiceOrderStatus.AGUARDANDO_APROVACAO,
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.FINALIZADA,
        ServiceOrderStatus.ENTREGUE,
    ):
        order.transition_to(target)
    assert order.status == ServiceOrderStatus.ENTREGUE
    assert order.started_at is not None
    assert order.completed_at is not None
    assert order.delivered_at is not None
