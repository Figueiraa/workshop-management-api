from app.application.dtos.client_dtos import CreateClientInput, UpdateClientInput
from app.application.ports.client_repository import ClientRepositoryPort
from app.domain.entities.client import Client
from app.domain.exceptions.domain_exceptions import ConflictError, NotFoundError


class ListClientsUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self._repo = repository

    async def execute(self) -> list[Client]:
        return await self._repo.get_all()


class GetClientUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self._repo = repository

    async def execute(self, client_id: int) -> Client:
        client = await self._repo.get_by_id(client_id)
        if not client:
            raise NotFoundError("Cliente", client_id)
        return client


class CreateClientUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self._repo = repository

    async def execute(self, data: CreateClientInput) -> Client:
        if await self._repo.get_by_cpf_cnpj(data.cpf_cnpj):
            raise ConflictError(f"CPF/CNPJ '{data.cpf_cnpj}' já cadastrado")
        client = Client(
            name=data.name,
            cpf_cnpj=data.cpf_cnpj,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )
        return await self._repo.add(client)


class UpdateClientUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self._repo = repository

    async def execute(self, client_id: int, data: UpdateClientInput) -> Client:
        client = await self._repo.get_by_id(client_id)
        if not client:
            raise NotFoundError("Cliente", client_id)
        if data.name is not None:
            client.name = data.name
        if data.phone is not None:
            client.phone = data.phone
        if data.email is not None:
            client.email = data.email
        if data.address is not None:
            client.address = data.address
        return await self._repo.update(client)


class DeleteClientUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self._repo = repository

    async def execute(self, client_id: int) -> None:
        client = await self._repo.get_by_id(client_id)
        if not client:
            raise NotFoundError("Cliente", client_id)
        await self._repo.delete(client_id)
