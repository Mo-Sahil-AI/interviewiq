import smtplib
from email.message import EmailMessage

from config import (
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USERNAME,
)


class EmailConfigurationError(RuntimeError):
    """SMTP is not configured sufficiently to send email."""


def ensure_configured() -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        raise EmailConfigurationError(
            "SMTP_HOST and SMTP_FROM_EMAIL must be configured"
        )


def send_email(recipient: str, subject: str, body: str) -> None:
    ensure_configured()

    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD or "")
        server.send_message(message)
