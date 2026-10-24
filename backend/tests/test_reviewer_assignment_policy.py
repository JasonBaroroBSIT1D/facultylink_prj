"""One active reviewer per faculty — assignment policy."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import FacultyProfile, User  # noqa: E402
from models.reviewer_assignment import ReviewerAssignment  # noqa: E402
from tests.helpers import delete_test_user_cascade  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402


def test_only_one_active_assignment_per_faculty():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    with app.app_context():
        faculty_id = (
            FacultyProfile.query.join(User).filter(User.email == "faculty@facultylink.edu").first().faculty_id
        )
        reviewer_a = User.query.filter_by(email="reviewer@facultylink.edu").first().user_id

    csrf = _fetch_csrf(client)
    email_b = f"reviewer-b-{uuid.uuid4().hex[:6]}@facultylink.test"
    reviewer_b: int | None = None
    try:
        created = client.post(
            "/api/v1/admin/users",
            json={"role": "reviewer", "email": email_b, "full_name": "Reviewer B", "password": "TempPass123"},
            headers={"X-CSRF-Token": csrf},
        )
        reviewer_b = created.get_json()["user"]["user_id"]

        csrf = _fetch_csrf(client)
        first = client.post(
            f"/api/v1/admin/reviewers/{reviewer_a}/assignments",
            json={"faculty_ids": [faculty_id]},
            headers={"X-CSRF-Token": csrf},
        )
        assert first.status_code == 201

        csrf = _fetch_csrf(client)
        second = client.post(
            f"/api/v1/admin/reviewers/{reviewer_b}/assignments",
            json={"faculty_ids": [faculty_id]},
            headers={"X-CSRF-Token": csrf},
        )
        assert second.status_code == 201

        with app.app_context():
            active = ReviewerAssignment.query.filter_by(faculty_id=faculty_id, is_active=True).all()
            assert len(active) == 1
            assert active[0].reviewer_id == reviewer_b

        rev_a = app.test_client()
        res = _login(rev_a, "reviewer@facultylink.edu", "demo-reviewer")
        _persist_web_cookie(rev_a, res)
        assert rev_a.get("/api/v1/reviewer/assigned-faculty").get_json()["faculty"] == []

        rev_b = app.test_client()
        res = _login(rev_b, email_b, "TempPass123", client_type="web")
        _persist_web_cookie(rev_b, res)
        rev_b.post(
            "/api/v1/auth/complete-mandatory-password",
            json={
                "temporary_password": "TempPass123",
                "new_password": "ReviewerPass123",
                "confirm_password": "ReviewerPass123",
            },
        )
        res = _login(rev_b, email_b, "ReviewerPass123", client_type="web")
        _persist_web_cookie(rev_b, res)
        listed = rev_b.get("/api/v1/reviewer/assigned-faculty").get_json()["faculty"]
        assert any(row["faculty_id"] == faculty_id for row in listed)
    finally:
        with app.app_context():
            ReviewerAssignment.query.filter_by(faculty_id=faculty_id).update({"is_active": False})
            db.session.commit()
        if reviewer_b is not None:
            with app.app_context():
                delete_test_user_cascade(reviewer_b)
        csrf = _fetch_csrf(client)
        client.post(
            f"/api/v1/admin/reviewers/{reviewer_a}/assignments",
            json={"faculty_ids": [faculty_id]},
            headers={"X-CSRF-Token": csrf},
        )


def test_assignment_candidates_show_elsewhere_reviewer():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    with app.app_context():
        faculty_id = (
            FacultyProfile.query.join(User).filter(User.email == "faculty@facultylink.edu").first().faculty_id
        )
        reviewer_a = User.query.filter_by(email="reviewer@facultylink.edu").first().user_id

    csrf = _fetch_csrf(client)
    email_b = f"reviewer-c-{uuid.uuid4().hex[:6]}@facultylink.test"
    reviewer_b: int | None = None
    try:
        created = client.post(
            "/api/v1/admin/users",
            json={"role": "reviewer", "email": email_b, "full_name": "Reviewer C", "password": "TempPass123"},
            headers={"X-CSRF-Token": csrf},
        )
        reviewer_b = created.get_json()["user"]["user_id"]

        csrf = _fetch_csrf(client)
        client.post(
            f"/api/v1/admin/reviewers/{reviewer_a}/assignments",
            json={"faculty_ids": [faculty_id]},
            headers={"X-CSRF-Token": csrf},
        )

        listed = client.get(f"/api/v1/admin/reviewers/{reviewer_b}/assignment-candidates")
        assert listed.status_code == 200
        row = next(c for c in listed.get_json()["candidates"] if c["faculty_id"] == faculty_id)
        assert row["assigned_elsewhere"] is True
        assert row["active_reviewer_id"] == reviewer_a
        assert row["active_assignment_id"]
    finally:
        with app.app_context():
            ReviewerAssignment.query.filter_by(faculty_id=faculty_id).update({"is_active": False})
            db.session.commit()
        if reviewer_b is not None:
            with app.app_context():
                delete_test_user_cascade(reviewer_b)
