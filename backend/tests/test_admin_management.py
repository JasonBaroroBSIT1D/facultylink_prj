"""Phase 4.4 admin faculty/reviewer management API tests."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from config import Config  # noqa: E402
from extensions import db  # noqa: E402
from models import User  # noqa: E402
from models.faculty_profile import FacultyProfile  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402


class TestConfig(Config):
    TESTING = True


def test_list_faculty_and_reviewers_from_db():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    faculty = client.get("/api/v1/admin/users?role=faculty")
    assert faculty.status_code == 200
    assert any(u["email"] == "faculty@facultylink.edu" for u in faculty.get_json()["users"])
    reviewers = client.get("/api/v1/admin/users?role=reviewer")
    assert reviewers.status_code == 200
    assert any(u["email"] == "reviewer@facultylink.edu" for u in reviewers.get_json()["users"])


def test_create_update_and_cleanup_accounts():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    faculty_email = f"faculty-{uuid.uuid4().hex[:8]}@facultylink.test"
    created = client.post(
        "/api/v1/admin/users",
        json={
            "role": "faculty",
            "email": faculty_email,
            "full_name": "Temp Faculty",
            "employee_number": f"EMP-{uuid.uuid4().hex[:6]}",
            "department": "Testing",
            "password": "TempPass123",
            "current_rank": "Instructor I",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201, created.get_json()
    user_id = created.get_json()["user"]["user_id"]

    csrf = _fetch_csrf(client)
    updated = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"department": "Updated Dept", "is_active": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.get_json()["user"]["faculty_profile"]["department"] == "Updated Dept"

    csrf = _fetch_csrf(client)
    dup = client.post(
        "/api/v1/admin/users",
        json={
            "role": "faculty",
            "email": faculty_email,
            "full_name": "Dup",
            "employee_number": f"EMP-{uuid.uuid4().hex[:6]}",
            "department": "X",
            "password": "TempPass123",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert dup.status_code == 409

    with app.app_context():
        db.session.query(FacultyProfile).filter_by(user_id=user_id).delete()
        db.session.query(User).filter_by(user_id=user_id).delete()
        db.session.commit()


def test_reviewer_forbidden_on_admin_users():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(client, res)
    assert client.get("/api/v1/admin/users?role=faculty").status_code == 403


def test_admin_cannot_deactivate_self():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    me = client.get("/api/v1/auth/me").get_json()["user"]
    csrf = _fetch_csrf(client)
    res = client.patch(
        f"/api/v1/admin/users/{me['user_id']}",
        json={"is_active": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert res.status_code == 403


if __name__ == "__main__":
    test_list_faculty_and_reviewers_from_db()
    test_create_update_and_cleanup_accounts()
    test_reviewer_forbidden_on_admin_users()
    test_admin_cannot_deactivate_self()
    print("All Phase 4.4 management tests passed.")
