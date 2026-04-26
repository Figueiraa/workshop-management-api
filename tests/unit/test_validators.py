import pytest
from pydantic import ValidationError

from app.schemas.client_schema import ClientCreate
from app.schemas.vehicle_schema import VehicleCreate


class TestCpfCnpjValidation:
    def test_valid_cpf(self):
        data = ClientCreate(name="João", cpf_cnpj="529.982.247-25")
        assert data.cpf_cnpj == "52998224725"

    def test_valid_cnpj(self):
        data = ClientCreate(name="Empresa", cpf_cnpj="11.222.333/0001-81")
        assert data.cpf_cnpj == "11222333000181"

    def test_invalid_cpf_raises(self):
        with pytest.raises(ValidationError):
            ClientCreate(name="João", cpf_cnpj="111.111.111-11")

    def test_invalid_cnpj_raises(self):
        with pytest.raises(ValidationError):
            ClientCreate(name="Empresa", cpf_cnpj="00.000.000/0000-00")

    def test_all_same_digits_cpf_raises(self):
        with pytest.raises(ValidationError):
            ClientCreate(name="João", cpf_cnpj="000.000.000-00")


class TestPlateValidation:
    def test_valid_old_format(self):
        data = VehicleCreate(plate="ABC-1234", brand="VW", model="Gol", year=2010, client_id=1)
        assert data.plate == "ABC1234"

    def test_valid_mercosul(self):
        data = VehicleCreate(plate="ABC1D23", brand="VW", model="Gol", year=2020, client_id=1)
        assert data.plate == "ABC1D23"

    def test_invalid_plate_raises(self):
        with pytest.raises(ValidationError):
            VehicleCreate(plate="INVALID", brand="VW", model="Gol", year=2020, client_id=1)

    def test_invalid_year_raises(self):
        with pytest.raises(ValidationError):
            VehicleCreate(plate="ABC1234", brand="VW", model="Gol", year=1800, client_id=1)


class TestStatusTransitions:
    def test_valid_transitions(self):
        from app.models.service_order_model import VALID_TRANSITIONS, ServiceOrderStatus

        assert ServiceOrderStatus.EM_DIAGNOSTICO in VALID_TRANSITIONS[ServiceOrderStatus.RECEBIDA]
        assert ServiceOrderStatus.EM_EXECUCAO in VALID_TRANSITIONS[ServiceOrderStatus.AGUARDANDO_APROVACAO]
        assert VALID_TRANSITIONS[ServiceOrderStatus.ENTREGUE] == []

    def test_no_skip_transitions(self):
        from app.models.service_order_model import VALID_TRANSITIONS, ServiceOrderStatus

        assert ServiceOrderStatus.EM_EXECUCAO not in VALID_TRANSITIONS[ServiceOrderStatus.RECEBIDA]
        assert ServiceOrderStatus.ENTREGUE not in VALID_TRANSITIONS[ServiceOrderStatus.EM_EXECUCAO]
