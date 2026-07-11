import logging
import smtplib
from email.message import EmailMessage

from app.application.ports.notifier import NotifierPort
from app.infrastructure.config import settings

logger = logging.getLogger("workshop.notifications")


class LoggingNotifier(NotifierPort):
    """Notificador padrão (dev/testes): registra a notificação em log."""

    async def notify_status_change(
        self, recipient: str | None, order_number: str, new_status: str
    ) -> None:
        logger.info(
            "Notificação de status da OS %s -> %s (destinatário: %s)",
            order_number,
            new_status,
            recipient or "não informado",
        )


class SmtpEmailNotifier(NotifierPort):
    """Notificador de produção: envia e-mail via SMTP. Falhas de envio são registradas,
    nunca propagadas (a notificação não deve derrubar o fluxo de negócio)."""

    async def notify_status_change(
        self, recipient: str | None, order_number: str, new_status: str
    ) -> None:
        if not recipient:
            logger.warning("OS %s sem e-mail de destinatário; notificação ignorada.", order_number)
            return

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = recipient
        message["Subject"] = f"Ordem de Serviço {order_number} — atualização de status"
        message.set_content(
            f"O status da sua Ordem de Serviço {order_number} foi atualizado para: {new_status}."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except OSError as exc:  # pragma: no cover - depende de ambiente SMTP externo
            logger.error("Falha ao enviar e-mail da OS %s: %s", order_number, exc)


def build_notifier() -> NotifierPort:
    """Escolhe o notificador conforme a configuração: SMTP se configurado, senão log."""
    if settings.SMTP_HOST:
        return SmtpEmailNotifier()
    return LoggingNotifier()
