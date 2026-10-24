"""Temporary-password onboarding and OTP password reset."""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from auth.mailer import MailDeliveryError  # noqa: E402
from auth.otp_service import _hash_otp  # noqa: E402
from auth.rate_limit import clear_rate_limits_for_tests  # noqa: E402
from extensions import db  # noqa: E402
from models import PasswordResetOtp, User  # noqa: E402
from tests.helpers import delete_test_user_cascade  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import EmailTestConfig  # noqa: E402


def _cleanup(app, user_id: int) -> None:
    with app.app_context():
        delete_test_user_cascade(user_id)


def test_create_faculty_sends_credentials_email():
    app = create_app(EmailTestConfig)
    bodies: list[str] = []
    client = app.test_client()
    _admin_cookie(client)

    def record(_to, _sub, body):
        bodies.append(body)

    with patch("auth.mailer._send_message", side_effect=record):
        csrf = _fetch_csrf(client)
        res = client.post(
            "/api/v1/admin/users",
            json={"role": "faculty", "email": f"f-{uuid.uuid4().hex[:6]}@facultylink.test", "full_name": "Faculty A"},
            headers={"X-CSRF-Token": csrf},
        )
    assert res.status_code == 201
    body = bodies[0]
    assert "Temporary Password:" in body
    assert "YOUR LOGIN CREDENTIALS" in body
    assert "GETTING STARTED" in body
    assert "Welcome to FacultyLink!" in body
    assert "one-time" not in body.lower()
    assert "invitation" not in body.lower()
    assert "127.0.0.1" not in body
    assert "WEB_PORTAL" not in body
    assert "password" not in res.get_json()
    assert res.get_json()["user"]["must_change_password"] is True
    _cleanup(app, res.get_json()["user"]["user_id"])


def test_faculty_login_forced_password_change():
    app = create_app(EmailTestConfig)
    client = app.test_client()
    _admin_cookie(client)
    captured: dict[str, str] = {}

    def record(_to, _sub, body):
        captured["body"] = body

    with patch("auth.mailer._send_message", side_effect=record):
        csrf = _fetch_csrf(client)
        email = f"fchg-{uuid.uuid4().hex[:6]}@facultylink.test"
        created = client.post(
            "/api/v1/admin/users",
            json={"role": "faculty", "email": email, "full_name": "Change Me"},
            headers={"X-CSRF-Token": csrf},
        )
    assert created.status_code == 201
    temp_line = [ln for ln in captured["body"].splitlines() if "Temporary Password:" in ln][0]
    temp = temp_line.split("Temporary Password:")[1].strip()
    user_id = created.get_json()["user"]["user_id"]

    mobile_client = app.test_client()
    login = _login(mobile_client, email, temp, "mobile")
    assert login.status_code == 200
    assert login.get_json()["must_change_password"] is True
    token = login.get_json()["access_token"]

    blocked = mobile_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["error"] == "password_change_required"

    # change password
    complete = mobile_client.post(
        "/api/v1/auth/complete-mandatory-password",
        json={"temporary_password": temp, "new_password": "NewPass123", "confirm_password": "NewPass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200, complete.get_json()

    login2 = _login(mobile_client, email, "NewPass123", "mobile")
    assert login2.status_code == 200
    assert login2.get_json()["must_change_password"] is False
    _cleanup(app, user_id)


def test_otp_forgot_password_flow():
    app = create_app(EmailTestConfig)
    email = f"otp-{uuid.uuid4().hex[:6]}@facultylink.test"
    user_id: int | None = None
    try:
        with app.app_context():
            from werkzeug.security import generate_password_hash

            user = User(
                email=email,
                password_hash=generate_password_hash("OldPass123"),
                role="reviewer",
                full_name="OTP User",
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.user_id

        otps: list[str] = []

        import re

        def record(_to, _sub, body):
            match = re.search(r"\b(\d{6})\b", body)
            if match:
                otps.append(match.group(1))

        client = app.test_client()
        with patch("auth.mailer._send_message", side_effect=record):
            req = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert req.status_code == 200
        assert otps
        otp = otps[0]

        bad = client.post("/api/v1/auth/forgot-password/verify-otp", json={"email": email, "otp": "000000"})
        assert bad.status_code == 400

        verify = client.post("/api/v1/auth/forgot-password/verify-otp", json={"email": email, "otp": otp})
        assert verify.status_code == 200
        grant = verify.get_json()["reset_grant"]

        done = client.post(
            "/api/v1/auth/forgot-password/complete",
            json={"email": email, "reset_grant": grant, "new_password": "Reset789x", "confirm_password": "Reset789x"},
        )
        assert done.status_code == 200
        login = _login(client, email, "Reset789x")
        assert login.status_code == 200
        assert _login(client, email, "OldPass123").status_code == 401
    finally:
        if user_id is not None:
            _cleanup(app, user_id)


def test_expired_otp_rejected():
    app = create_app(EmailTestConfig)
    with app.app_context():
        from werkzeug.security import generate_password_hash

        email = f"exp-{uuid.uuid4().hex[:6]}@facultylink.test"
        user = User(email=email, password_hash=generate_password_hash("x"), role="reviewer", full_name="X", is_active=True)
        db.session.add(user)
        db.session.commit()
        otp = "123456"
        row = PasswordResetOtp(
            user_id=user.user_id,
            otp_hash=_hash_otp(user.user_id, otp),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            failed_attempts=0,
        )
        db.session.add(row)
        db.session.commit()
        user_id = user.user_id

    client = app.test_client()
    res = client.post("/api/v1/auth/forgot-password/verify-otp", json={"email": email, "otp": otp})
    assert res.status_code == 400
    _cleanup(app, user_id)


def test_resend_credentials_rotates_temp_password():
    app = create_app(EmailTestConfig)
    client = app.test_client()
    _admin_cookie(client)
    emails: list[str] = []

    def record(_to, _sub, body):
        emails.append(body)

    with patch("auth.mailer._send_message", side_effect=record):
        csrf = _fetch_csrf(client)
        created = client.post(
            "/api/v1/admin/users",
            json={
                "role": "reviewer",
                "email": f"rs-{uuid.uuid4().hex[:6]}@facultylink.test",
                "full_name": "Resend Test",
            },
            headers={"X-CSRF-Token": csrf},
        )
    assert created.status_code == 201
    user_id = created.get_json()["user"]["user_id"]
    first_temp = [ln for ln in emails[0].splitlines() if "Temporary Password:" in ln][0].split("Temporary Password:")[1].strip()

    with patch("auth.mailer._send_message", side_effect=record):
        csrf = _fetch_csrf(client)
        resent = client.post(
            f"/api/v1/admin/users/{user_id}/resend-invitation",
            headers={"X-CSRF-Token": csrf},
        )
    assert resent.status_code == 200
    assert resent.get_json()["email_delivery"]["sent"] is True
    assert resent.get_json()["user"]["must_change_password"] is True
    second_temp = [ln for ln in emails[1].splitlines() if "Temporary Password:" in ln][0].split("Temporary Password:")[1].strip()
    assert first_temp != second_temp

    login_old = _login(client, created.get_json()["user"]["email"], first_temp, client_type="web")
    assert login_old.status_code == 401
    login_new = _login(client, created.get_json()["user"]["email"], second_temp, client_type="web")
    assert login_new.status_code == 200
    assert login_new.get_json()["must_change_password"] is True
    _cleanup(app, user_id)


def test_smtp_failure_keeps_account():
    app = create_app(EmailTestConfig)
    client = app.test_client()
    _admin_cookie(client)

    def fail(*_a, **_k):
        raise MailDeliveryError("fail")

    with patch("auth.mailer._send_message", side_effect=fail):
        csrf = _fetch_csrf(client)
        res = client.post(
            "/api/v1/admin/users",
            json={"role": "reviewer", "email": f"fail-{uuid.uuid4().hex[:6]}@facultylink.test", "full_name": "Fail"},
            headers={"X-CSRF-Token": csrf},
        )
    assert res.status_code == 201
    body = res.get_json()
    assert body["email_delivery"]["sent"] is False
    assert body["user"]["credentials_delivery_pending"] is True
    _cleanup(app, body["user"]["user_id"])
