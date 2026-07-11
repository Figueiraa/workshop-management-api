import enum


class ServiceOrderStatus(str, enum.Enum):
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    EM_EXECUCAO = "EM_EXECUCAO"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    ORCAMENTO_RECUSADO = "ORCAMENTO_RECUSADO"


# Status terminais: OS encerradas, ocultadas da listagem de trabalho ativo.
TERMINAL_STATUSES: list[ServiceOrderStatus] = [
    ServiceOrderStatus.FINALIZADA,
    ServiceOrderStatus.ENTREGUE,
    ServiceOrderStatus.ORCAMENTO_RECUSADO,
]

# Máquina de estados da Ordem de Serviço: para cada status, os status para os quais
# é permitido transicionar. Regra de negócio pertencente ao domínio.
VALID_TRANSITIONS: dict[ServiceOrderStatus, list[ServiceOrderStatus]] = {
    ServiceOrderStatus.RECEBIDA: [ServiceOrderStatus.EM_DIAGNOSTICO],
    ServiceOrderStatus.EM_DIAGNOSTICO: [ServiceOrderStatus.AGUARDANDO_APROVACAO],
    ServiceOrderStatus.AGUARDANDO_APROVACAO: [
        ServiceOrderStatus.EM_EXECUCAO,
        ServiceOrderStatus.ORCAMENTO_RECUSADO,
    ],
    ServiceOrderStatus.EM_EXECUCAO: [ServiceOrderStatus.FINALIZADA],
    ServiceOrderStatus.FINALIZADA: [ServiceOrderStatus.ENTREGUE],
    ServiceOrderStatus.ENTREGUE: [],
    ServiceOrderStatus.ORCAMENTO_RECUSADO: [],
}
