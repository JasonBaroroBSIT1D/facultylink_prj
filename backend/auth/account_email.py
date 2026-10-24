from __future__ import annotations

from auth.mailer import MailDeliveryError, send_welcome_credentials_email
from models import User


def deliver_account_credentials(user: User, temporary_password: str) -> dict:
    """Email temporary credentials. Plaintext password must not be logged or returned in API."""
    from flask import current_app

    current_app.logger.info(
        "Delivering welcome credentials email to user_id=%s role=%s (temporary_password not logged)",
        user.user_id,
        user.role,
    )
    try:
        send_welcome_credentials_email(
            to_email=user.email,
            full_name=user.full_name,
            role=user.role,
            temporary_password=temporary_password,
        )
        user.credentials_delivery_pending = False
        from extensions import db

        db.session.commit()
        return {"sent": True, "message": "Account credentials email sent."}
    except MailDeliveryError as exc:
        user.credentials_delivery_pending = True
        from extensions import db

        db.session.commit()
        return {"sent": False, "message": str(exc)}
