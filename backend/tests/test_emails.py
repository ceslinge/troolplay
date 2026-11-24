import smtplib
from email.message import EmailMessage
from typing import ClassVar, Self

import pytest

from backend.accounts import emails
from backend.config import settings


class FakeSMTP:
    """Un serveur SMTP qui n'envoie rien : il retient ce qu'on lui confie."""

    instances: ClassVar[list["FakeSMTP"]] = []
    fail_with: ClassVar[Exception | None] = None

    def __init__(self, host: str, port: int, context=None, timeout=None) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self.logged_in: tuple[str, str] | None = None
        self.sent: list[EmailMessage] = []
        FakeSMTP.instances.append(self)
        if FakeSMTP.fail_with:
            raise FakeSMTP.fail_with

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        pass

    def login(self, user: str, password: str) -> None:
        self.logged_in = (user, password)

    def send_message(self, message: EmailMessage) -> None:
        self.sent.append(message)


@pytest.fixture
def smtp(monkeypatch: pytest.MonkeyPatch) -> type[FakeSMTP]:
    FakeSMTP.instances = []
    FakeSMTP.fail_with = None
    monkeypatch.setattr(emails.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(settings, "smtp_host", "smtp.exemple.test")
    monkeypatch.setattr(settings, "smtp_port", 465)
    monkeypatch.setattr(settings, "smtp_user", "contact@exemple.test")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "mail_from", "")
    return FakeSMTP


def test_without_smtp_the_email_shows_in_the_terminal(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(settings, "smtp_host", "")

    emails.send_email("joueur@example.com", "Bonjour", "Le corps.")

    out = capsys.readouterr().out
    assert "joueur@example.com" in out
    assert "Le corps." in out


def test_with_smtp_the_email_leaves_signed_in(smtp: type[FakeSMTP]) -> None:
    emails.send_email("joueur@example.com", "Bonjour", "Le corps.")

    (server,) = smtp.instances
    assert (server.host, server.port) == ("smtp.exemple.test", 465)
    assert server.logged_in == ("contact@exemple.test", "secret")
    (message,) = server.sent
    assert message["To"] == "joueur@example.com"
    assert message["Subject"] == "Bonjour"
    assert message["From"] == "tRoolPlay <contact@exemple.test>"
    assert message["Date"] and message["Message-ID"].endswith("@exemple.test>")
    assert message.get_content().strip() == "Le corps."


def test_the_sender_can_differ_from_the_smtp_account(
    smtp: type[FakeSMTP], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "mail_from", "ne-pas-repondre@exemple.test")

    emails.send_email("joueur@example.com", "Bonjour", "Le corps.")

    assert smtp.instances[0].sent[0]["From"] == (
        "tRoolPlay <ne-pas-repondre@exemple.test>"
    )


@pytest.mark.parametrize(
    "failure", [smtplib.SMTPAuthenticationError(535, b"non"), TimeoutError()]
)
def test_a_failed_send_is_logged_without_the_address(
    smtp: type[FakeSMTP], caplog: pytest.LogCaptureFixture, failure: Exception
) -> None:
    smtp.fail_with = failure

    emails.send_email("joueur@example.com", "Changer ton mot de passe", "…")

    assert "Changer ton mot de passe" in caplog.text
    assert "joueur@example.com" not in caplog.text


def test_signup_sends_its_email_after_answering(client, outbox) -> None:
    response = client.post(
        "/accounts",
        json={
            "email": "nouveau@example.com",
            "password": "une phrase de passe assez longue",
            "accept_rules": True,
            "age_confirmed": True,
        },
    )

    assert response.status_code == 202
    assert [mail["to"] for mail in outbox] == ["nouveau@example.com"]
