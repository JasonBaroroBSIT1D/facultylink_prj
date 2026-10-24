"""Phase 4.3 authentication and user management tests (isolated TEST_DATABASE_URL)."""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from auth.jwt_service import clear_revoked_for_tests  # noqa: E402
from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import User  # noqa: E402
from tests.test_config import IsolatedTestConfig  # noqa: E402


class TestConfig(IsolatedTestConfig):
    JWT_ACCESS_TTL_SECONDS = 3600


def _login(client, email, password, client_type="web"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "client": client_type},
    )


def _persist_web_cookie(client, response):
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("facultylink_access="):
            token = header.split(";", 1)[0].split("=", 1)[1]
            client.set_cookie("facultylink_access", token, path="/")
            client.environ_base["HTTP_COOKIE"] = f"facultylink_access={token}"
            return token
    return None


def _admin_cookie(client):
    clear_revoked_for_tests()
    res = _login(client, "admin@facultylink.edu", "demo-admin")
    assert res.status_code == 200, res.get_json()
    assert _persist_web_cookie(client, res)
    return res


def test_admin_login_and_me():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _admin_cookie(client)
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["role"] == "admin"


def test_reviewer_login():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "reviewer@facultylink.edu", "demo-reviewer")
    assert res.status_code == 200
    assert res.get_json()["user"]["role"] == "reviewer"
    _persist_web_cookie(client, res)


def test_faculty_mobile_login():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    assert res.status_code == 200
    body = res.get_json()
    assert body.get("access_token")
    assert body["user"]["role"] == "faculty"


def test_wrong_password_and_unknown_email():
    app = create_app(TestConfig)
    client = app.test_client()
    assert _login(client, "admin@facultylink.edu", "wrong").status_code == 401
    assert _login(client, "missing@facultylink.edu", "demo-admin").status_code == 401


def test_faculty_blocked_on_web_client():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "faculty@facultylink.edu", "demo-faculty", "web")
    assert res.status_code == 403


def test_inactive_account():
    app = create_app(TestConfig)
    email = f"inactive-{uuid.uuid4().hex[:8]}@facultylink.test"
    with app.app_context():
        from werkzeug.security import generate_password_hash

        user = User(
            email=email,
            password_hash=generate_password_hash("TestPass123"),
            role="reviewer",
            full_name="Inactive Test",
            is_active=False,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id
    client = app.test_client()
    res = _login(client, email, "anything")
    assert res.status_code == 403
    with app.app_context():
        db.session.query(User).filter_by(user_id=user_id).delete()
        db.session.commit()


def _fetch_csrf(client):
    res = client.get("/api/v1/auth/csrf")
    assert res.status_code == 200
    token = res.get_json()["csrf_token"]
    client.environ_base["HTTP_COOKIE"] = client.environ_base.get("HTTP_COOKIE", "") + f"; facultylink_csrf={token}"
    return token


def test_logout_invalidates_session():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    assert client.get("/api/v1/auth/me").status_code == 200
    token = _fetch_csrf(client)
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_reviewer_cannot_list_admin_users():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(client, res)
    res = client.get("/api/v1/admin/users")
    assert res.status_code == 403


def test_admin_create_duplicate_and_new_faculty():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    email = f"faculty-{uuid.uuid4().hex[:8]}@facultylink.test"
    payload = {
        "email": email,
        "password": "TempPass123",
        "role": "faculty",
        "full_name": "Temp Faculty",
        "employee_number": f"EMP-{uuid.uuid4().hex[:6]}",
        "college": "Test",
        "department": "Test",
    }
    csrf = _fetch_csrf(client)
    created = client.post("/api/v1/admin/users", json=payload, headers={"X-CSRF-Token": csrf})
    assert created.status_code == 201, created.get_json()
    user_id = created.get_json()["user"]["user_id"]
    csrf = _fetch_csrf(client)
    dup = client.post("/api/v1/admin/users", json=payload, headers={"X-CSRF-Token": csrf})
    assert dup.status_code == 409
    with app.app_context():
        from models.faculty_profile import FacultyProfile

        db.session.query(FacultyProfile).filter_by(user_id=user_id).delete()
        db.session.query(User).filter_by(user_id=user_id).delete()
        db.session.commit()


def test_token_expiration():
    class ShortLivedConfig(TestConfig):
        JWT_ACCESS_TTL_SECONDS = 1

    app = create_app(ShortLivedConfig)
    client = app.test_client()
    _admin_cookie(client)
    time.sleep(2.1)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_change_password_flow():
    app = create_app(TestConfig)
    email = f"pw-{uuid.uuid4().hex[:8]}@facultylink.test"
    with app.app_context():
        from werkzeug.security import generate_password_hash

        user = User(
            email=email,
            password_hash=generate_password_hash("OldPass123"),
            role="reviewer",
            full_name="Password Test",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
    client = app.test_client()
    login_res = _login(client, email, "OldPass123")
    _persist_web_cookie(client, login_res)
    token = _fetch_csrf(client)
    res = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass456"},
        headers={"X-CSRF-Token": token},
    )
    assert res.status_code == 200, res.get_json()
    assert client.get("/api/v1/auth/me").status_code == 401
    again = _login(client, email, "NewPass456")
    assert again.status_code == 200
    _persist_web_cookie(client, again)
    with app.app_context():
        db.session.query(User).filter_by(email=email).delete()
        db.session.commit()


if __name__ == "__main__":
    tests = [
        test_admin_login_and_me,
        test_reviewer_login,
        test_faculty_mobile_login,
        test_wrong_password_and_unknown_email,
        test_faculty_blocked_on_web_client,
        test_inactive_account,
        test_logout_invalidates_session,
        test_reviewer_cannot_list_admin_users,
        test_admin_create_duplicate_and_new_faculty,
        test_token_expiration,
        test_change_password_flow,
    ]
    for fn in tests:
        fn()
        print("OK", fn.__name__)
    print("All Phase 4.3 auth tests passed.")
