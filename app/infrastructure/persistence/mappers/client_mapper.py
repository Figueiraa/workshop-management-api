from app.domain.entities.client import Client
from app.infrastructure.persistence.models.client_model import Client as ClientModel


def to_domain(model: ClientModel) -> Client:
    return Client(
        id=model.id,
        name=model.name,
        cpf_cnpj=model.cpf_cnpj,
        phone=model.phone,
        email=model.email,
        address=model.address,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
