import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.dtos.auth_dtos import RegisterUserInput
from app.application.dtos.client_dtos import CreateClientInput, UpdateClientInput
from app.application.dtos.part_dtos import CreatePartInput, UpdatePartInput
from app.application.dtos.service_order_dtos import OpenServiceOrderInput, OpenServiceOrderPartInput
from app.application.dtos.service_type_dtos import CreateServiceTypeInput, UpdateServiceTypeInput
from app.application.dtos.vehicle_dtos import CreateVehicleInput, UpdateVehicleInput
from app.application.use_cases.auth import AuthenticateUserUseCase, RegisterUserUseCase
from app.application.use_cases.client import (
    CreateClientUseCase,
    DeleteClientUseCase,
    GetClientUseCase,
    ListClientsUseCase,
    UpdateClientUseCase,
)
from app.application.use_cases.get_average_execution_time import GetAverageExecutionTimeUseCase
from app.application.use_cases.open_service_order import OpenServiceOrderUseCase
from app.application.use_cases.part import (
    AdjustPartStockUseCase,
    CreatePartUseCase,
    DeletePartUseCase,
    GetPartUseCase,
    UpdatePartUseCase,
)
from app.application.use_cases.service_type import (
    CreateServiceTypeUseCase,
    GetServiceTypeUseCase,
    UpdateServiceTypeUseCase,
)
from app.application.use_cases.update_service_order_status import UpdateServiceOrderStatusUseCase
from app.application.use_cases.vehicle import (
    CreateVehicleUseCase,
    DeleteVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesByClientUseCase,
    UpdateVehicleUseCase,
)
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleError,
    ConflictError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    NotFoundError,
    UnauthorizedError,
)
from app.domain.value_objects.service_order_status import ServiceOrderStatus
from app.infrastructure.database import Base
from app.infrastructure.persistence.gateways.service_order_gateways import (
    SqlAlchemyPartGateway,
    SqlAlchemyServiceTypeGateway,
    SqlAlchemyVehicleGateway,
)
from app.infrastructure.persistence.repositories.client_repository import SqlAlchemyClientRepository
from app.infrastructure.persistence.repositories.part_repository import SqlAlchemyPartRepository
from app.infrastructure.persistence.repositories.service_order_repository import (
    SqlAlchemyServiceOrderRepository,
)
from app.infrastructure.persistence.repositories.service_type_repository import (
    SqlAlchemyServiceTypeRepository,
)
from app.infrastructure.persistence.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.persistence.repositories.vehicle_repository import SqlAlchemyVehicleRepository
from app.infrastructure.security.security import PasswordHasher, TokenIssuer

TEST_URL = "sqlite+aiosqlite:///:memory:"

CPF = "52998224725"


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


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _register(session: AsyncSession) -> RegisterUserUseCase:
    return RegisterUserUseCase(SqlAlchemyUserRepository(session), PasswordHasher())


def _authenticate(session: AsyncSession) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(SqlAlchemyUserRepository(session), PasswordHasher(), TokenIssuer())


@pytest.mark.asyncio
async def test_register_success(session: AsyncSession):
    user = await _register(session).execute(RegisterUserInput(username="admin", email="a@x.com", password="pass"))
    assert user.username == "admin"
    assert user.password_hash != "pass"


@pytest.mark.asyncio
async def test_register_duplicate_username_raises(session: AsyncSession):
    await _register(session).execute(RegisterUserInput(username="admin", email="a@x.com", password="p"))
    with pytest.raises(ConflictError):
        await _register(session).execute(RegisterUserInput(username="admin", email="b@x.com", password="p"))


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(session: AsyncSession):
    await _register(session).execute(RegisterUserInput(username="u1", email="same@x.com", password="p"))
    with pytest.raises(ConflictError):
        await _register(session).execute(RegisterUserInput(username="u2", email="same@x.com", password="p"))


@pytest.mark.asyncio
async def test_login_success(session: AsyncSession):
    await _register(session).execute(RegisterUserInput(username="admin", email="a@x.com", password="pass"))
    token = await _authenticate(session).execute("admin", "pass")
    assert isinstance(token, str) and len(token) > 0


@pytest.mark.asyncio
async def test_login_wrong_password_raises(session: AsyncSession):
    await _register(session).execute(RegisterUserInput(username="admin", email="a@x.com", password="pass"))
    with pytest.raises(UnauthorizedError):
        await _authenticate(session).execute("admin", "errada")


@pytest.mark.asyncio
async def test_login_unknown_user_raises(session: AsyncSession):
    with pytest.raises(UnauthorizedError):
        await _authenticate(session).execute("ghost", "x")


# ─── Client ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_client_create_and_list(session: AsyncSession):
    repo = SqlAlchemyClientRepository(session)
    await CreateClientUseCase(repo).execute(CreateClientInput(name="João", cpf_cnpj=CPF))
    clients = await ListClientsUseCase(repo).execute()
    assert len(clients) == 1


@pytest.mark.asyncio
async def test_client_get_by_id(session: AsyncSession):
    repo = SqlAlchemyClientRepository(session)
    created = await CreateClientUseCase(repo).execute(CreateClientInput(name="Maria", cpf_cnpj=CPF))
    found = await GetClientUseCase(repo).execute(created.id)
    assert found.id == created.id


@pytest.mark.asyncio
async def test_client_get_by_id_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await GetClientUseCase(SqlAlchemyClientRepository(session)).execute(9999)


@pytest.mark.asyncio
async def test_client_duplicate_cpf_raises(session: AsyncSession):
    repo = SqlAlchemyClientRepository(session)
    await CreateClientUseCase(repo).execute(CreateClientInput(name="A", cpf_cnpj=CPF))
    with pytest.raises(ConflictError):
        await CreateClientUseCase(repo).execute(CreateClientInput(name="B", cpf_cnpj=CPF))


@pytest.mark.asyncio
async def test_client_update(session: AsyncSession):
    repo = SqlAlchemyClientRepository(session)
    c = await CreateClientUseCase(repo).execute(CreateClientInput(name="João", cpf_cnpj=CPF))
    updated = await UpdateClientUseCase(repo).execute(c.id, UpdateClientInput(name="Maria"))
    assert updated.name == "Maria"


@pytest.mark.asyncio
async def test_client_update_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await UpdateClientUseCase(SqlAlchemyClientRepository(session)).execute(9999, UpdateClientInput(name="X"))


@pytest.mark.asyncio
async def test_client_delete(session: AsyncSession):
    repo = SqlAlchemyClientRepository(session)
    c = await CreateClientUseCase(repo).execute(CreateClientInput(name="João", cpf_cnpj=CPF))
    await DeleteClientUseCase(repo).execute(c.id)
    with pytest.raises(NotFoundError):
        await GetClientUseCase(repo).execute(c.id)


@pytest.mark.asyncio
async def test_client_delete_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await DeleteClientUseCase(SqlAlchemyClientRepository(session)).execute(9999)


# ─── Vehicle ──────────────────────────────────────────────────────────────────

async def _make_client(session: AsyncSession):
    return await CreateClientUseCase(SqlAlchemyClientRepository(session)).execute(
        CreateClientInput(name="João", cpf_cnpj=CPF)
    )


def _create_vehicle(session: AsyncSession) -> CreateVehicleUseCase:
    return CreateVehicleUseCase(SqlAlchemyVehicleRepository(session), SqlAlchemyClientRepository(session))


@pytest.mark.asyncio
async def test_vehicle_create(session: AsyncSession):
    c = await _make_client(session)
    v = await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id)
    )
    assert v.plate == "ABC1234"


@pytest.mark.asyncio
async def test_vehicle_create_client_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await _create_vehicle(session).execute(
            CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=9999)
        )


@pytest.mark.asyncio
async def test_vehicle_create_duplicate_plate_raises(session: AsyncSession):
    c = await _make_client(session)
    await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id)
    )
    with pytest.raises(ConflictError):
        await _create_vehicle(session).execute(
            CreateVehicleInput(plate="ABC1234", brand="Fiat", model="Uno", year=2019, client_id=c.id)
        )


@pytest.mark.asyncio
async def test_vehicle_list_by_client(session: AsyncSession):
    c = await _make_client(session)
    await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id)
    )
    use_case = ListVehiclesByClientUseCase(SqlAlchemyVehicleRepository(session), SqlAlchemyClientRepository(session))
    result = await use_case.execute(c.id)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_vehicle_list_by_invalid_client_raises(session: AsyncSession):
    use_case = ListVehiclesByClientUseCase(SqlAlchemyVehicleRepository(session), SqlAlchemyClientRepository(session))
    with pytest.raises(NotFoundError):
        await use_case.execute(9999)


@pytest.mark.asyncio
async def test_vehicle_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await GetVehicleUseCase(SqlAlchemyVehicleRepository(session)).execute(9999)


@pytest.mark.asyncio
async def test_vehicle_update(session: AsyncSession):
    c = await _make_client(session)
    v = await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id)
    )
    updated = await UpdateVehicleUseCase(SqlAlchemyVehicleRepository(session)).execute(
        v.id, UpdateVehicleInput(model="Fox")
    )
    assert updated.model == "Fox"


@pytest.mark.asyncio
async def test_vehicle_delete(session: AsyncSession):
    c = await _make_client(session)
    v = await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=c.id)
    )
    await DeleteVehicleUseCase(SqlAlchemyVehicleRepository(session)).execute(v.id)
    with pytest.raises(NotFoundError):
        await GetVehicleUseCase(SqlAlchemyVehicleRepository(session)).execute(v.id)


# ─── ServiceType ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_service_type_create_and_get(session: AsyncSession):
    repo = SqlAlchemyServiceTypeRepository(session)
    st = await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="Troca de óleo", price=100.0))
    found = await GetServiceTypeUseCase(repo).execute(st.id)
    assert found.name == "Troca de óleo"


@pytest.mark.asyncio
async def test_service_type_duplicate_name_raises(session: AsyncSession):
    repo = SqlAlchemyServiceTypeRepository(session)
    await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="Alinhamento", price=80.0))
    with pytest.raises(ConflictError):
        await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="Alinhamento", price=90.0))


@pytest.mark.asyncio
async def test_service_type_update(session: AsyncSession):
    repo = SqlAlchemyServiceTypeRepository(session)
    st = await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="Revisão", price=200.0))
    updated = await UpdateServiceTypeUseCase(repo).execute(st.id, UpdateServiceTypeInput(price=250.0))
    assert updated.price == 250.0


@pytest.mark.asyncio
async def test_service_type_update_name_conflict_raises(session: AsyncSession):
    repo = SqlAlchemyServiceTypeRepository(session)
    await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="A", price=100.0))
    st = await CreateServiceTypeUseCase(repo).execute(CreateServiceTypeInput(name="B", price=200.0))
    with pytest.raises(ConflictError):
        await UpdateServiceTypeUseCase(repo).execute(st.id, UpdateServiceTypeInput(name="A"))


@pytest.mark.asyncio
async def test_service_type_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await GetServiceTypeUseCase(SqlAlchemyServiceTypeRepository(session)).execute(9999)


# ─── Part ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_part_create_and_get(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Filtro", unit_price=30.0, stock_quantity=10))
    found = await GetPartUseCase(repo).execute(p.id)
    assert found.stock_quantity == 10


@pytest.mark.asyncio
async def test_part_get_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await GetPartUseCase(SqlAlchemyPartRepository(session)).execute(9999)


@pytest.mark.asyncio
async def test_part_update(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Vela", unit_price=15.0, stock_quantity=5))
    updated = await UpdatePartUseCase(repo).execute(p.id, UpdatePartInput(unit_price=20.0))
    assert updated.unit_price == 20.0


@pytest.mark.asyncio
async def test_part_adjust_stock_add(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Óleo", unit_price=40.0, stock_quantity=5))
    updated = await AdjustPartStockUseCase(repo).execute(p.id, 10)
    assert updated.stock_quantity == 15


@pytest.mark.asyncio
async def test_part_adjust_stock_remove(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Óleo", unit_price=40.0, stock_quantity=10))
    updated = await AdjustPartStockUseCase(repo).execute(p.id, -3)
    assert updated.stock_quantity == 7


@pytest.mark.asyncio
async def test_part_adjust_stock_below_zero_raises(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Óleo", unit_price=40.0, stock_quantity=2))
    with pytest.raises(BusinessRuleError):
        await AdjustPartStockUseCase(repo).execute(p.id, -10)


@pytest.mark.asyncio
async def test_part_delete(session: AsyncSession):
    repo = SqlAlchemyPartRepository(session)
    p = await CreatePartUseCase(repo).execute(CreatePartInput(name="Parafuso", unit_price=2.0, stock_quantity=100))
    await DeletePartUseCase(repo).execute(p.id)
    with pytest.raises(NotFoundError):
        await GetPartUseCase(repo).execute(p.id)


# ─── ServiceOrder ─────────────────────────────────────────────────────────────

async def _setup_order_prerequisites(session: AsyncSession):
    client = await _make_client(session)
    vehicle = await _create_vehicle(session).execute(
        CreateVehicleInput(plate="ABC1234", brand="VW", model="Gol", year=2020, client_id=client.id)
    )
    service_type = await CreateServiceTypeUseCase(SqlAlchemyServiceTypeRepository(session)).execute(
        CreateServiceTypeInput(name="Troca de óleo", price=150.0)
    )
    part = await CreatePartUseCase(SqlAlchemyPartRepository(session)).execute(
        CreatePartInput(name="Óleo", unit_price=45.0, stock_quantity=10)
    )
    return vehicle, service_type, part


def _open_order(session: AsyncSession) -> OpenServiceOrderUseCase:
    return OpenServiceOrderUseCase(
        SqlAlchemyServiceOrderRepository(session),
        SqlAlchemyVehicleGateway(session),
        SqlAlchemyServiceTypeGateway(session),
        SqlAlchemyPartGateway(session),
    )


@pytest.mark.asyncio
async def test_order_create(session: AsyncSession):
    vehicle, _, part = await _setup_order_prerequisites(session)
    order = await _open_order(session).execute(
        OpenServiceOrderInput(
            vehicle_id=vehicle.id,
            parts=[OpenServiceOrderPartInput(part_id=part.id, quantity=2)],
        )
    )
    assert order.status == ServiceOrderStatus.RECEBIDA
    assert order.total_budget == 45.0 * 2
    assert order.number.startswith("OS")


@pytest.mark.asyncio
async def test_order_create_vehicle_not_found_raises(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await _open_order(session).execute(OpenServiceOrderInput(vehicle_id=9999))


@pytest.mark.asyncio
async def test_order_create_insufficient_stock_raises(session: AsyncSession):
    vehicle, _, part = await _setup_order_prerequisites(session)
    with pytest.raises(InsufficientStockError):
        await _open_order(session).execute(
            OpenServiceOrderInput(
                vehicle_id=vehicle.id,
                parts=[OpenServiceOrderPartInput(part_id=part.id, quantity=999)],
            )
        )


@pytest.mark.asyncio
async def test_order_status_full_flow(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    order = await _open_order(session).execute(OpenServiceOrderInput(vehicle_id=vehicle.id))
    update = UpdateServiceOrderStatusUseCase(SqlAlchemyServiceOrderRepository(session))
    for target in [
        ServiceOrderStatus.EM_DIAGNOSTICO,
        ServiceOrderStatus.AGUARDANDO_APROVACAO,
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.FINALIZADA,
        ServiceOrderStatus.ENTREGUE,
    ]:
        order = await update.execute(order.id, target)
        assert order.status == target
    assert order.started_at is not None
    assert order.completed_at is not None
    assert order.delivered_at is not None


@pytest.mark.asyncio
async def test_order_invalid_transition_raises(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    order = await _open_order(session).execute(OpenServiceOrderInput(vehicle_id=vehicle.id))
    update = UpdateServiceOrderStatusUseCase(SqlAlchemyServiceOrderRepository(session))
    with pytest.raises(InvalidStatusTransitionError):
        await update.execute(order.id, ServiceOrderStatus.ENTREGUE)


@pytest.mark.asyncio
async def test_order_update_status_not_found_raises(session: AsyncSession):
    update = UpdateServiceOrderStatusUseCase(SqlAlchemyServiceOrderRepository(session))
    with pytest.raises(NotFoundError):
        await update.execute(9999, ServiceOrderStatus.EM_DIAGNOSTICO)


@pytest.mark.asyncio
async def test_order_average_execution_time_no_data(session: AsyncSession):
    result = await GetAverageExecutionTimeUseCase(SqlAlchemyServiceOrderRepository(session)).execute()
    assert result.total_completed == 0
    assert result.average_minutes is None


@pytest.mark.asyncio
async def test_order_average_execution_time_with_data(session: AsyncSession):
    vehicle, _, _ = await _setup_order_prerequisites(session)
    order = await _open_order(session).execute(OpenServiceOrderInput(vehicle_id=vehicle.id))
    update = UpdateServiceOrderStatusUseCase(SqlAlchemyServiceOrderRepository(session))
    for target in [
        ServiceOrderStatus.EM_DIAGNOSTICO,
        ServiceOrderStatus.AGUARDANDO_APROVACAO,
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.FINALIZADA,
        ServiceOrderStatus.ENTREGUE,
    ]:
        order = await update.execute(order.id, target)
    result = await GetAverageExecutionTimeUseCase(SqlAlchemyServiceOrderRepository(session)).execute()
    assert result.total_completed == 1
    assert result.average_minutes is not None
