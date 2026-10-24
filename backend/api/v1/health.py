from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify

from auth import mailer as mailer_module
from db.schema import check_database_connection, verify_public_schema
from extensions import db

bp = Blueprint("health_v1", __name__)


@bp.get("/health")
def health():
    service = current_app.config.get("API_SERVICE_NAME", "FacultyLink API")
    try:
        engine = db.engine
        check_database_connection(engine)
        schema_ok, issues = verify_public_schema(engine)
        if not schema_ok:
            current_app.logger.warning("Schema verification failed: %s", "; ".join(issues))
            return (
                jsonify(
                    {
                        "status": "error",
                        "service": service,
                        "database": "connected",
                        "error": "schema_mismatch",
                        "message": "Database connected but schema does not match expected FacultyLink tables.",
                        "details": issues,
                    }
                ),
                503,
            )
        mailer_path = Path(mailer_module.__file__).resolve()
        payload = {
            "status": "ok",
            "service": service,
            "database": "connected",
            "auth_onboarding": {
                "mode": "temporary_password",
                "create_account_email": "send_welcome_credentials_email",
                "resend_credentials_email": "send_welcome_credentials_email",
                "forgot_password": "otp_6_digit",
                "invitation_setup_codes": False,
                "mailer_module": str(mailer_path),
            },
        }
        return jsonify(payload), 200
    except Exception as exc:
        current_app.logger.error("Health check database failure: %s", exc.__class__.__name__)
        return (
            jsonify(
                {
                    "status": "error",
                    "service": service,
                    "database": "unavailable",
                    "error": "database_unavailable",
                    "message": "Could not connect to PostgreSQL.",
                }
            ),
            503,
        )
