"""Testes do serviço de notificação (canal de log e canal de e-mail/SMTP)."""

import logging
import smtplib
from email.message import EmailMessage

import pytest

from app.infrastructure.notifications import notifier as notifier_module
from app.infrastructure.notifications.notifier import (
    CHANNEL_EMAIL,
    CHANNEL_LOG,
    RESULT_FAILED,
    RESULT_SENT,
    RESULT_SKIPPED,
    LoggingNotifier,
    SmtpEmailNotifier,
    build_notifier,
)
from app.infrastructure.observability.metrics import notifications_total


def _notifications(channel: str, result: str) -> float:
    """Lê o valor atual do contador de notificações para o par canal/resultado."""
    return float(notifications_total.labels(channel=channel, result=result)._value.get())


class FakeSmtp:
    """Dublê do `smtplib.SMTP`, usado como context manager pelo notificador."""

    instances: list["FakeSmtp"] = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent: list[EmailMessage] = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, message):
        self.sent.append(message)


@pytest.fixture(autouse=True)
def _reset_fake_smtp():
    FakeSmtp.instances = []
    yield
    FakeSmtp.instances = []


class TestLoggingNotifier:
    async def test_registra_notificacao_em_log(self, caplog):
        with caplog.at_level(logging.INFO, logger="workshop.notifications"):
            await LoggingNotifier().notify_status_change("cliente@teste.com", "OS-001", "EM_EXECUCAO")

        assert "OS-001" in caplog.text
        assert "EM_EXECUCAO" in caplog.text
        assert "cliente@teste.com" in caplog.text

    async def test_registra_mesmo_sem_destinatario(self, caplog):
        with caplog.at_level(logging.INFO, logger="workshop.notifications"):
            await LoggingNotifier().notify_status_change(None, "OS-002", "FINALIZADA")

        assert "nao informado" in caplog.text.replace("ã", "a")

    async def test_contabiliza_metrica_de_notificacao(self):
        antes = _notifications(CHANNEL_LOG, RESULT_SENT)
        await LoggingNotifier().notify_status_change("cliente@teste.com", "OS-003", "ENTREGUE")
        assert _notifications(CHANNEL_LOG, RESULT_SENT) == antes + 1

    async def test_sem_destinatario_conta_como_skipped(self):
        antes = _notifications(CHANNEL_LOG, RESULT_SKIPPED)
        await LoggingNotifier().notify_status_change(None, "OS-004", "ENTREGUE")
        assert _notifications(CHANNEL_LOG, RESULT_SKIPPED) == antes + 1


class TestSmtpEmailNotifier:
    async def test_envia_email_com_assunto_e_corpo(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        monkeypatch.setattr(notifier_module.settings, "SMTP_PORT", 2525)
        monkeypatch.setattr(notifier_module.settings, "SMTP_USER", None)
        monkeypatch.setattr(notifier_module.settings, "SMTP_PASSWORD", None)
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", FakeSmtp)

        await SmtpEmailNotifier().notify_status_change("cliente@teste.com", "OS-010", "EM_EXECUCAO")

        server = FakeSmtp.instances[0]
        assert (server.host, server.port) == ("smtp.teste.com", 2525)
        assert server.started_tls is True
        assert len(server.sent) == 1
        message = server.sent[0]
        assert message["To"] == "cliente@teste.com"
        assert "OS-010" in message["Subject"]
        assert "EM_EXECUCAO" in message.get_content()

    async def test_autentica_quando_ha_credenciais(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        monkeypatch.setattr(notifier_module.settings, "SMTP_USER", "usuario")
        monkeypatch.setattr(notifier_module.settings, "SMTP_PASSWORD", "segredo")
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", FakeSmtp)

        await SmtpEmailNotifier().notify_status_change("cliente@teste.com", "OS-011", "FINALIZADA")

        assert FakeSmtp.instances[0].login_args == ("usuario", "segredo")

    async def test_nao_abre_conexao_sem_destinatario(self, monkeypatch):
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", FakeSmtp)
        antes = _notifications(CHANNEL_EMAIL, RESULT_SKIPPED)

        await SmtpEmailNotifier().notify_status_change(None, "OS-012", "FINALIZADA")

        assert FakeSmtp.instances == []
        assert _notifications(CHANNEL_EMAIL, RESULT_SKIPPED) == antes + 1

    async def test_falha_de_envio_nao_propaga_e_e_registrada(self, monkeypatch, caplog):
        def explode(*_args, **_kwargs):
            raise smtplib.SMTPException("servidor indisponivel")

        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", explode)
        antes = _notifications(CHANNEL_EMAIL, RESULT_FAILED)

        with caplog.at_level(logging.ERROR, logger="workshop.notifications"):
            # Nao deve levantar: a notificacao nunca derruba o fluxo de negocio.
            await SmtpEmailNotifier().notify_status_change("cliente@teste.com", "OS-013", "ENTREGUE")

        assert "OS-013" in caplog.text
        assert _notifications(CHANNEL_EMAIL, RESULT_FAILED) == antes + 1

    async def test_erro_de_rede_tambem_e_tratado(self, monkeypatch):
        def explode(*_args, **_kwargs):
            raise OSError("connection refused")

        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", explode)

        await SmtpEmailNotifier().notify_status_change("cliente@teste.com", "OS-014", "ENTREGUE")

    async def test_sem_tls_quando_desabilitado(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        monkeypatch.setattr(notifier_module.settings, "SMTP_USE_TLS", False)
        monkeypatch.setattr(notifier_module.smtplib, "SMTP", FakeSmtp)

        await SmtpEmailNotifier().notify_status_change("cliente@teste.com", "OS-015", "RECEBIDA")

        assert FakeSmtp.instances[0].started_tls is False


class TestBuildNotifier:
    def test_padrao_e_o_notificador_de_log(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "NOTIFICATION_CHANNEL", "auto")
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", None)
        assert isinstance(build_notifier(), LoggingNotifier)

    def test_auto_escolhe_email_quando_ha_smtp_host(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "NOTIFICATION_CHANNEL", "auto")
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        assert isinstance(build_notifier(), SmtpEmailNotifier)

    def test_canal_email_forcado(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "NOTIFICATION_CHANNEL", "EMAIL")
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        assert isinstance(build_notifier(), SmtpEmailNotifier)

    def test_canal_log_forcado_ignora_smtp_host(self, monkeypatch):
        monkeypatch.setattr(notifier_module.settings, "NOTIFICATION_CHANNEL", "log")
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", "smtp.teste.com")
        assert isinstance(build_notifier(), LoggingNotifier)

    def test_email_sem_smtp_host_cai_para_log(self, monkeypatch, caplog):
        monkeypatch.setattr(notifier_module.settings, "NOTIFICATION_CHANNEL", "email")
        monkeypatch.setattr(notifier_module.settings, "SMTP_HOST", None)

        with caplog.at_level(logging.WARNING, logger="workshop.notifications"):
            notifier = build_notifier()

        assert isinstance(notifier, LoggingNotifier)
        assert "SMTP_HOST" in caplog.text
