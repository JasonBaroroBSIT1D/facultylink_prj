from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)


class MailDeliveryError(Exception):
    pass


def _role_label(role: str) -> str:
    return {"faculty": "Faculty", "reviewer": "Reviewer", "admin": "Administrator"}.get(role, role.title())


def _access_channel(role: str) -> str:
    if role == "faculty":
        return "FacultyLink Mobile Application"
    if role == "reviewer":
        return "FacultyLink Reviewer Web Portal"
    return "FacultyLink Admin Web Portal"


def _send_message(to_email: str, subject: str, body_text: str) -> None:
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        logger.info("Mail suppressed (test mode) to=%s subject=%s", to_email, subject)
        return

    from config import Config

    if not Config.smtp_configured():
        raise MailDeliveryError("SMTP is not configured.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["SMTP_FROM_EMAIL"]
    msg["To"] = to_email
    msg.set_content(body_text)

    host = current_app.config["SMTP_HOST"]
    port = int(current_app.config["SMTP_PORT"])
    username = current_app.config["SMTP_USERNAME"]
    password = current_app.config["SMTP_PASSWORD"]
    use_tls = current_app.config.get("SMTP_USE_TLS", True)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
    except Exception as exc:
        logger.warning("SMTP delivery failed for %s: %s", to_email, exc.__class__.__name__)
        raise MailDeliveryError("Unable to deliver email.") from exc


def send_welcome_credentials_email(
    *,
    to_email: str,
    full_name: str,
    role: str,
    temporary_password: str,
) -> None:
    role_label = _role_label(role)
    channel = _access_channel(role)
    ttl_hours = int(current_app.config.get("TEMP_PASSWORD_TTL_HOURS", 72))
    body = (
        f"Hello {full_name},\n\n"
        "Welcome to FacultyLink!\n\n"
        f"Your {role_label} account has been successfully created by the System Administrator.\n\n"
        "YOUR LOGIN CREDENTIALS\n\n"
        f"Registered Email: {to_email}\n\n"
        f"Temporary Password: {temporary_password}\n\n"
        "GETTING STARTED\n\n"
        f"1. Open the {channel}.\n"
        "2. Sign in using your registered email and temporary password.\n"
        "3. You will be required to create a new password on your first login.\n"
        "4. After changing your password, you can access your dashboard.\n\n"
        "For security, do not share your temporary password.\n\n"
        "If you did not expect this account, please contact your system administrator.\n\n"
        "Best regards,\n"
        "FacultyLink Support Team\n"
    )
    _send_message(to_email, "Welcome to FacultyLink — Your Login Credentials", body)


def send_password_otp_email(*, to_email: str, full_name: str, otp_code: str) -> None:
    ttl_min = max(1, int(current_app.config.get("OTP_TTL_SECONDS", 300)) // 60)
    body = (
        f"Hello {full_name},\n\n"
        "We received a request to reset your FacultyLink password.\n\n"
        f"Your verification code is:\n\n"
        f"{otp_code}\n\n"
        f"This code will expire in {ttl_min} minutes.\n\n"
        "If you did not request a password reset, you can safely ignore this email.\n\n"
        "Please do not share this verification code.\n\n"
        "Best regards,\n\n"
        "FacultyLink Support Team\n"
    )
    _send_message(to_email, "FacultyLink — Password Reset Verification Code", body)
