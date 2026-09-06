"""Adapters do serviço de notificação de mudança de status da Ordem de Serviço.

Implementam a porta `NotifierPort` (camada de aplicação) em dois canais:

* `LoggingNotifier` — registra a notificação como log estruturado (JSON). É o
  padrão em desenvolvimento/testes e serve de trilha de auditoria em produção.
* `SmtpEmailNotifier` — envia o e-mail ao cliente via SMTP e **também** registra
  o log, para que o envio seja rastreável.

A escolha do canal é feita por configuração em `build_notifier()`: basta definir
`SMTP_HOST` (ou `NOTIFICATION_CHANNEL=email`) para ativar o envio real, sem
qualquer alteração nos casos de uso.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.application.ports.notifier import NotifierPort
from app.infrastructure.config import settings
from app.infrastructure.observability.metrics import record_notification

logger = logging.getLogger("workshop.notifications")

CHANNEL_LOG = "log"
CHANNEL_EMAIL = "email"

RESULT_SENT = "sent"
RESULT_SKIPPED = "skipped"
RESULT_FAILED = "failed"


def _build_message(recipient: str, order_number: str, new_status: str) -> EmailMessage:
    """Monta o e-mail de aviso de mudança de status enviado ao cliente."""
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = f"Ordem de Serviço {order_number} — atualização de status"
    message.set_content(
        f"Olá!\n\n"
        f"O status da sua Ordem de Serviço {order_number} foi atualizado para: {new_status}.\n\n"
        f"Você pode consultar os detalhes a qualquer momento pelo número da OS.\n\n"
        f"Oficina Mecânica — mensagem automática, não responda este e-mail."
    )
    return message


class LoggingNotifier(NotifierPort):
    """Notificador padrão: registra a notificação em log estruturado."""

    channel = CHANNEL_LOG

    async def notify_status_change(
        self, recipient: str | None, order_number: str, new_status: str
    ) -> None:
        logger.info(
            "Notificação de status da OS %s -> %s (destinatário: %s)",
            order_number,
            new_status,
            recipient or "não informado",
        )
        record_notification(
            channel=CHANNEL_LOG, result=RESULT_SENT if recipient else RESULT_SKIPPED
        )


class SmtpEmailNotifier(NotifierPort):
    """Notificador de produção: envia e-mail via SMTP.

    Falhas de envio são registradas e contabilizadas, nunca propagadas — uma
    indisponibilidade do servidor de e-mail não pode derrubar o fluxo de negócio
    (a OS já foi atualizada com sucesso quando a notificação é disparada).
    """

    channel = CHANNEL_EMAIL

    async def notify_status_change(
        self, recipient: str | None, order_number: str, new_status: str
    ) -> None:
        if not recipient:
            logger.warning("OS %s sem e-mail de destinatário; notificação ignorada.", order_number)
            record_notification(channel=CHANNEL_EMAIL, result=RESULT_SKIPPED)
            return

        message = _build_message(recipient, order_number, new_status)
        try:
            # smtplib é bloqueante: roda numa thread para não travar o event loop.
            await asyncio.to_thread(self._send, message)
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("Falha ao enviar e-mail da OS %s: %s", order_number, exc)
            record_notification(channel=CHANNEL_EMAIL, result=RESULT_FAILED)
            return

        logger.info(
            "E-mail de status da OS %s -> %s enviado para %s", order_number, new_status, recipient
        )
        record_notification(channel=CHANNEL_EMAIL, result=RESULT_SENT)

    @staticmethod
    def _send(message: EmailMessage) -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)


def build_notifier() -> NotifierPort:
    """Seleciona o canal de notificação conforme a configuração.

    `NOTIFICATION_CHANNEL=email` (ou, por conveniência, apenas definir `SMTP_HOST`)
    ativa o envio por e-mail; caso contrário, usa o notificador de log.
    """
    channel = settings.NOTIFICATION_CHANNEL.strip().lower()
    if channel == CHANNEL_EMAIL or (channel == "auto" and settings.SMTP_HOST):
        if not settings.SMTP_HOST:
            logger.warning(
                "NOTIFICATION_CHANNEL=email sem SMTP_HOST configurado; usando notificador de log."
            )
            return LoggingNotifier()
        return SmtpEmailNotifier()
    return LoggingNotifier()
