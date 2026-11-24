"""Les emails du site.

En développement (SMTP_HOST vide), rien ne part : chaque email s'affiche dans le terminal
du backend. En production, ils partent par le SMTP configuré dans .env.

Les routes les envoient en tâche de fond, après la réponse : un envoi prend une seconde
ou deux, et un temps de réponse plus long trahirait qu'une adresse a un compte.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from backend.config import settings

log = logging.getLogger(__name__)

SENDER_NAME = "TroolPlay"


def build_message(to: str, subject: str, body: str) -> EmailMessage:
    sender = settings.mail_from or settings.smtp_user
    message = EmailMessage()
    message["From"] = formataddr((SENDER_NAME, sender))
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=sender.rpartition("@")[2] or None)
    message.set_content(body)
    return message


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        print(
            f"\n--- Email pour {to} ---\nObjet : {subject}\n\n{body}\n---\n", flush=True
        )
        return
    try:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            context=ssl.create_default_context(),
            timeout=15,
        ) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(build_message(to, subject, body))
    except (smtplib.SMTPException, OSError):
        # La réponse est déjà partie : on le note, sans l'adresse (les journaux ne la gardent pas).
        log.exception("Email non envoyé : %s", subject)
