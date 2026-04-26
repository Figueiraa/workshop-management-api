import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.exceptions.domain_exceptions import (
    BusinessRuleError,
    ConflictError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.models.service_order_model import ServiceOrderStatus
from app.schemas.auth_schema import UserCreate
from app.schemas.client_schema import ClientCreate, ClientUpdate
from app.schemas.part_schema import PartCreate, PartUpdate
from app.schemas.service_order_schema import ServiceOrderCreate, ServiceOrderItemInput, ServiceOrderPartInput
from app.schemas.service_type_schema import ServiceTypeCreate, ServiceTypeUpdate
from app.schemas.vehicle_schema import VehicleCreate, VehicleUpdate
from app.services.auth_service import AuthService
from app.services.client_service import ClientService
from app.services.part_service import PartService
from app.services.service_order_service import ServiceOrderService
from app.services.service_type_service import ServiceTypeService
from app.services.vehicle_service import VehicleService

TEST_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(loop_scope="function")
async def session():
    engine = create_async_engine(TEST_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ─── AuthService ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_register_success(session: AsyncSession):
    svc = AuthService(session)
    user = await svc.register(UserCreate(username="admin", email="a@x.com", password="pass"))
    assert user.username == "admin"
    assert user.password_hash != "pass"


@pytest.mark.asyncio
async def test_auth_register_duplicate_username_raises(session: AsyncSession):
    svc = AuthService(session)
    await svc.register(UserCreate(username="admin", email="a@x.com", password="p"))
    with pytest.raises(ConflictError):
        await svc.register(UserCreate(username="admin", email="b@x.com", password="p"))


@pytest.mark.asyncio
async def test_auth_register_duplicate_email_raises(session: AsyncSession):
    svc = AuthService(session)
    await svc.register(UserCreate(username="u1", email="same@x.com", password="p"))
    with pytest.raises(ConflictError):
        await svc.register(UserCreate(username="u2", email="same@x.com", password="p"))


@pytest.mark.asyncio
async def test_auth_login_success(session: AsyncSession):
    svc = AuthService(session)
    await svc.register(UserCreate(username="admin", email="a@x.com", password="pass"))
    token = await svc.login("admin", "pass")
    assert isinstance(token, str) and len(token) > 0


@pytest.mark.asyncio
async def test_auth_login_wrong_password_raises(session: AsyncSession):
    svc = AuthService(session)
    await svc.register(UserCreate(username="admin", email="a@x.com", password="pass"))
    with pytest.raises(NotFoundError):
        await svc.login("admin", "errada")


@pytest.mark.asyncio
async def test_auth_login_unknown_user_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await AuthService(session).login("ghost", "x")


# ─── ClientService ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_client_create_and_list(session: AsyncSession):
    svc = ClientService(session)
    await svc.create(ClientCreate(name="João", cpf_cnpj="529.982.247-25"))
    clients = await svc.list_all()
    assert len(clients) == 1


@pytest.mark.asyncio
async def test_client_get_by_id(session: AsyncSession):
    svc = ClientService(session)
    created = await svc.create(ClientCreate(name="Maria", cpf_cnpj="529.982.247-25"))
    found = await svc.get_by_id(created.id)
    assert found.id == created.id


@pytest.mark.asyncio
async def test_client_get_by_id_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ClientService(session).get_by_id(9999)


@pytest.mark.asyncio
async def test_client_duplicate_cpf_raises(session: AsyncSession):
    svc = ClientService(session)
    await svc.create(ClientCreate(name="A", cpf_cnpj="529.982.247-25"))
    with pytest.raises(ConflictError):
        await svc.create(ClientCreate(name="B", cpf_cnpj="529.982.247-25"))


@pytest.mark.asyncio
async def test_client_update(session: AsyncSession):
    svc = ClientService(session)
    c = await svc.create(ClientCreate(name="João", cpf_cnpj="529.982.247-25"))
    updated = await svc.update(c.id, ClientUpdate(name="Maria"))
    assert updated.name == "Maria"


@pytest.mark.asyncio
async def test_client_update_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ClientService(session).update(9999, ClientUpdate(name="X"))


@pytest.mark.asyncio
async def test_client_delete(session: AsyncSession):
    svc = ClientService(session)
    c = await svc.create(ClientCreate(name="João", cpf_cnpj="529.982.247-25"))
    await svc.delete(c.id)
    with pytest.raises(NotFoundError):
        await svc.get_by_id(c.id)


@pytest.mark.asyncio
async def test_client_delete_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ClientService(session).delete(9999)


# ─── VehicleService ─────────────────────────────────────────────────────────

async def _make_client(session: AsyncSession):
    return await ClientService(session).create(ClientCreate(name="João", cpf_cnpj="529.982.247-25"))


@pytest.mark.asyncio
async def test_vehicle_create(session: AsyncSession):
    c = await _make_client(session)
    svc = VehicleService(session)
    v = await svc.create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    assert v.plate == "ABC1234"


@pytest.mark.asyncio
async def test_vehicle_create_client_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await VehicleService(session).create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=9999))


@pytest.mark.asyncio
async def test_vehicle_create_duplicate_plate_raises(session: AsyncSession):
    c = await _make_client(session)
    svc = VehicleService(session)
    await svc.create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    with pytest.raises(ConflictError):
        await svc.create(VehicleCreate(plate="ABC1234", brand="Fiat", model="Uno", year=2019, client_id=c.id))


@pytest.mark.asyncio
async def test_vehicle_list_all(session: AsyncSession):
    c = await _make_client(session)
    await VehicleService(session).create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    result = await VehicleService(session).list_all()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_vehicle_list_by_client(session: AsyncSession):
    c = await _make_client(session)
    await VehicleService(session).create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    result = await VehicleService(session).list_by_client(c.id)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_vehicle_list_by_invalid_client_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await VehicleService(session).list_by_client(9999)


@pytest.mark.asyncio
async def test_vehicle_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await VehicleService(session).get_by_id(9999)


@pytest.mark.asyncio
async def test_vehicle_update(session: AsyncSession):
    c = await _make_client(session)
    v = await VehicleService(session).create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    updated = await VehicleService(session).update(v.id, VehicleUpdate(model="Fox"))
    assert updated.model == "Fox"


@pytest.mark.asyncio
async def test_vehicle_update_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await VehicleService(session).update(9999, VehicleUpdate(model="X"))


@pytest.mark.asyncio
async def test_vehicle_delete(session: AsyncSession):
    c = await _make_client(session)
    v = await VehicleService(session).create(VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id))
    await VehicleService(session).delete(v.id)
    with pytest.raises(NotFoundError):
        await VehicleService(session).get_by_id(v.id)


@pytest.mark.asyncio
async def test_vehicle_delete_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await VehicleService(session).delete(9999)


# ─── ServiceTypeService ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_service_type_create_and_list(session: AsyncSession):
    svc = ServiceTypeService(session)
    await svc.create(ServiceTypeCreate(name="Troca de óleo", price=100.0))
    result = await svc.list_all()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_service_type_duplicate_name_raises(session: AsyncSession):
    svc = ServiceTypeService(session)
    await svc.create(ServiceTypeCreate(name="Alinhamento", price=80.0))
    with pytest.raises(ConflictError):
        await svc.create(ServiceTypeCreate(name="Alinhamento", price=90.0))


@pytest.mark.asyncio
async def test_service_type_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceTypeService(session).get_by_id(9999)


@pytest.mark.asyncio
async def test_service_type_update(session: AsyncSession):
    svc = ServiceTypeService(session)
    st = await svc.create(ServiceTypeCreate(name="Revisão", price=200.0))
    updated = await svc.update(st.id, ServiceTypeUpdate(price=250.0))
    assert updated.price == 250.0


@pytest.mark.asyncio
async def test_service_type_update_name_conflict_raises(session: AsyncSession):
    svc = ServiceTypeService(session)
    await svc.create(ServiceTypeCreate(name="A", price=100.0))
    st = await svc.create(ServiceTypeCreate(name="B", price=200.0))
    with pytest.raises(ConflictError):
        await svc.update(st.id, ServiceTypeUpdate(name="A"))


@pytest.mark.asyncio
async def test_service_type_update_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceTypeService(session).update(9999, ServiceTypeUpdate(price=10.0))


@pytest.mark.asyncio
async def test_service_type_delete(session: AsyncSession):
    svc = ServiceTypeService(session)
    st = await svc.create(ServiceTypeCreate(name="Pintura", price=500.0))
    await svc.delete(st.id)
    with pytest.raises(NotFoundError):
        await svc.get_by_id(st.id)


@pytest.mark.asyncio
async def test_service_type_delete_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceTypeService(session).delete(9999)


# ─── PartService ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_part_create_and_list(session: AsyncSession):
    svc = PartService(session)
    await svc.create(PartCreate(name="Filtro", unit_price=30.0, stock_quantity=10))
    result = await svc.list_all()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_part_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await PartService(session).get_by_id(9999)


@pytest.mark.asyncio
async def test_part_update(session: AsyncSession):
    svc = PartService(session)
    p = await svc.create(PartCreate(name="Vela", unit_price=15.0, stock_quantity=5))
    updated = await svc.update(p.id, PartUpdate(unit_price=20.0))
    assert updated.unit_price == 20.0


@pytest.mark.asyncio
async def test_part_update_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await PartService(session).update(9999, PartUpdate(unit_price=10.0))


@pytest.mark.asyncio
async def test_part_adjust_stock_add(session: AsyncSession):
    svc = PartService(session)
    p = await svc.create(PartCreate(name="Óleo", unit_price=40.0, stock_quantity=5))
    updated = await svc.adjust_stock(p.id, 10)
    assert updated.stock_quantity == 15


@pytest.mark.asyncio
async def test_part_adjust_stock_remove(session: AsyncSession):
    svc = PartService(session)
    p = await svc.create(PartCreate(name="Óleo", unit_price=40.0, stock_quantity=10))
    updated = await svc.adjust_stock(p.id, -3)
    assert updated.stock_quantity == 7


@pytest.mark.asyncio
async def test_part_adjust_stock_below_zero_raises(session: AsyncSession):
    svc = PartService(session)
    p = await svc.create(PartCreate(name="Óleo", unit_price=40.0, stock_quantity=2))
    with pytest.raises(BusinessRuleError):
        await svc.adjust_stock(p.id, -10)


@pytest.mark.asyncio
async def test_part_adjust_stock_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await PartService(session).adjust_stock(9999, 5)


@pytest.mark.asyncio
async def test_part_delete(session: AsyncSession):
    svc = PartService(session)
    p = await svc.create(PartCreate(name="Parafuso", unit_price=2.0, stock_quantity=100))
    await svc.delete(p.id)
    with pytest.raises(NotFoundError):
        await svc.get_by_id(p.id)


@pytest.mark.asyncio
async def test_part_delete_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await PartService(session).delete(9999)


# ─── ServiceOrderService ────────────────────────────────────────────────────

async def _setup_order_prerequisites(session: AsyncSession):
    client = await ClientService(session).create(ClientCreate(name="João", cpf_cnpj="529.982.247-25"))
    vehicle = await VehicleService(session).create(
        VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=client.id)
    )
    service_type = await ServiceTypeService(session).create(
        ServiceTypeCreate(name="Troca de óleo", price=150.0)
    )
    part = await PartService(session).create(
        PartCreate(name="Óleo", unit_price=45.0, stock_quantity=10)
    )
    return vehicle, service_type, part


@pytest.mark.asyncio
async def test_order_create(session: AsyncSession):
    vehicle, service_type, part = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    order = await svc.create(ServiceOrderCreate(
        vehicle_id=vehicle.id,
        items=[ServiceOrderItemInput(service_type_id=service_type.id, quantity=1)],
        parts=[ServiceOrderPartInput(part_id=part.id, quantity=2)],
    ))
    assert order.status == ServiceOrderStatus.RECEBIDA
    assert order.total_budget == 150.0 + 45.0 * 2
    assert order.number.startswith("OS")


@pytest.mark.asyncio
async def test_order_create_vehicle_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceOrderService(session).create(ServiceOrderCreate(vehicle_id=9999))


@pytest.mark.asyncio
async def test_order_create_service_type_not_found_raises(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    with pytest.raises(NotFoundError):
        await ServiceOrderService(session).create(ServiceOrderCreate(
            vehicle_id=vehicle.id,
            items=[ServiceOrderItemInput(service_type_id=9999)],
        ))


@pytest.mark.asyncio
async def test_order_create_part_not_found_raises(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    with pytest.raises(NotFoundError):
        await ServiceOrderService(session).create(ServiceOrderCreate(
            vehicle_id=vehicle.id,
            parts=[ServiceOrderPartInput(part_id=9999, quantity=1)],
        ))


@pytest.mark.asyncio
async def test_order_create_insufficient_stock_raises(session: AsyncSession):
    vehicle, _, part = await _setup_order_prerequisites(session)
    with pytest.raises(InsufficientStockError):
        await ServiceOrderService(session).create(ServiceOrderCreate(
            vehicle_id=vehicle.id,
            parts=[ServiceOrderPartInput(part_id=part.id, quantity=999)],
        ))


@pytest.mark.asyncio
async def test_order_list_all(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))
    result = await svc.list_all()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_order_get_by_id(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    order = await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))
    found = await svc.get_by_id(order.id)
    assert found.id == order.id


@pytest.mark.asyncio
async def test_order_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceOrderService(session).get_by_id(9999)


@pytest.mark.asyncio
async def test_order_list_by_status(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))
    result = await svc.list_by_status(ServiceOrderStatus.RECEBIDA)
    assert len(result) == 1
    result = await svc.list_by_status(ServiceOrderStatus.ENTREGUE)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_order_status_full_flow(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    order = await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))

    for status in [
        ServiceOrderStatus.EM_DIAGNOSTICO,
        ServiceOrderStatus.AGUARDANDO_APROVACAO,
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.FINALIZADA,
        ServiceOrderStatus.ENTREGUE,
    ]:
        order = await svc.update_status(order.id, status)
        assert order.status == status

    assert order.started_at is not None
    assert order.completed_at is not None
    assert order.delivered_at is not None


@pytest.mark.asyncio
async def test_order_invalid_transition_raises(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    order = await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))
    with pytest.raises(InvalidStatusTransitionError):
        await svc.update_status(order.id, ServiceOrderStatus.ENTREGUE)


@pytest.mark.asyncio
async def test_order_update_status_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await ServiceOrderService(session).update_status(9999, ServiceOrderStatus.EM_DIAGNOSTICO)


@pytest.mark.asyncio
async def test_order_average_execution_time_no_data(session: AsyncSession):
    result = await ServiceOrderService(session).get_average_execution_time()
    assert result.total_completed == 0
    assert result.average_minutes is None


@pytest.mark.asyncio
async def test_order_average_execution_time_with_data(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    svc = ServiceOrderService(session)
    order = await svc.create(ServiceOrderCreate(vehicle_id=vehicle.id))
    for status in [
        ServiceOrderStatus.EM_DIAGNOSTICO,
        ServiceOrderStatus.AGUARDANDO_APROVACAO,
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.FINALIZADA,
        ServiceOrderStatus.ENTREGUE,
    ]:
        order = await svc.update_status(order.id, status)

    result = await svc.get_average_execution_time()
    assert result.total_completed == 1
    assert result.average_minutes is not None
