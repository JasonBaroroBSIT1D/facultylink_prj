"""Post Phase 4.5 integration updates."""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import FacultyProfile, User  # noqa: E402
from models.evaluation_period import EvaluationPeriod  # noqa: E402
from tests.helpers import delete_test_user_cascade  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402
from api.v1.reviewer_queue import queue_count_for_reviewer  # noqa: E402


def test_reviewer_queue_count_matches_service():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    with app.app_context():
        reviewer_id = User.query.filter_by(email="reviewer@facultylink.edu").with_entities(User.user_id).scalar()
        expected = queue_count_for_reviewer(reviewer_id)
    listed = client.get("/api/v1/admin/users?role=reviewer")
    assert listed.status_code == 200
    row = next(u for u in listed.get_json()["users"] if u["email"] == "reviewer@facultylink.edu")
    assert row["queue_count"] == expected


def test_reassign_moves_faculty_between_reviewers():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    with app.app_context():
        faculty_id = FacultyProfile.query.join(User).filter(User.email == "faculty@facultylink.edu").first().faculty_id
        reviewer_a = User.query.filter_by(email="reviewer@facultylink.edu").first().user_id
    csrf = _fetch_csrf(client)
    email = f"reviewer2-{uuid.uuid4().hex[:6]}@facultylink.test"
    reviewer_b: int | None = None
    assignment_id: int | None = None
    try:
        created = client.post(
            "/api/v1/admin/users",
            json={"role": "reviewer", "email": email, "full_name": "Temp Reviewer 2", "password": "TempPass123"},
            headers={"X-CSRF-Token": csrf},
        )
        reviewer_b = created.get_json()["user"]["user_id"]

        csrf = _fetch_csrf(client)
        assign = client.post(
            f"/api/v1/admin/reviewers/{reviewer_a}/assignments",
            json={"faculty_ids": [faculty_id]},
            headers={"X-CSRF-Token": csrf},
        )
        assignment_id = assign.get_json()["assignments"][0]["assignment_id"]

        csrf = _fetch_csrf(client)
        moved = client.patch(
            f"/api/v1/admin/reviewer-assignments/{assignment_id}",
            json={"reviewer_id": reviewer_b},
            headers={"X-CSRF-Token": csrf},
        )
        assert moved.status_code == 200

        rev_a = app.test_client()
        res = _login(rev_a, "reviewer@facultylink.edu", "demo-reviewer")
        _persist_web_cookie(rev_a, res)
        assert rev_a.get("/api/v1/reviewer/assigned-faculty").get_json()["faculty"] == []

        rev_b = app.test_client()
        res = _login(rev_b, email, "TempPass123", client_type="web")
        _persist_web_cookie(rev_b, res)
        changed = rev_b.post(
            "/api/v1/auth/complete-mandatory-password",
            json={
                "temporary_password": "TempPass123",
                "new_password": "ReviewerPass123",
                "confirm_password": "ReviewerPass123",
            },
        )
        assert changed.status_code == 200, changed.get_json()
        res = _login(rev_b, email, "ReviewerPass123", client_type="web")
        _persist_web_cookie(rev_b, res)
        assigned = rev_b.get("/api/v1/reviewer/assigned-faculty").get_json()
        assert any(f["faculty_id"] == faculty_id for f in assigned["faculty"])
    finally:
        if assignment_id is not None:
            csrf = _fetch_csrf(client)
            client.patch(
                f"/api/v1/admin/reviewer-assignments/{assignment_id}",
                json={"reviewer_id": reviewer_a},
                headers={"X-CSRF-Token": csrf},
            )
        if reviewer_b is not None:
            with app.app_context():
                delete_test_user_cascade(reviewer_b)


def test_faculty_read_only_evaluation_periods():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "faculty@facultylink.edu", "demo-faculty", client_type="mobile")
    token = res.get_json()["access_token"]
    periods = client.get("/api/v1/evaluation-periods", headers={"Authorization": f"Bearer {token}"})
    assert periods.status_code == 200
    denied = client.post(
        "/api/v1/admin/evaluation-periods",
        json={"name": "X", "academicYear": "X", "semester": "X", "opensAt": "2026-01-01T08:00:00+08:00", "closesAt": "2026-02-01T08:00:00+08:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 403


def test_close_early_updates_period():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    now = datetime.now(timezone.utc)
    period = EvaluationPeriod(
        name="Close early test",
        academic_year="2025-2026",
        semester="Test",
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(days=5),
        submission_enabled=True,
        review_enabled=True,
    )
    with app.app_context():
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id

    csrf = _fetch_csrf(client)
    closed = client.post(
        f"/api/v1/admin/evaluation-periods/{period_id}/close-early",
        headers={"X-CSRF-Token": csrf},
    )
    assert closed.status_code == 200
    assert closed.get_json()["period"]["status"] == "Closed"

    with app.app_context():
        db.session.query(EvaluationPeriod).filter_by(period_id=period_id).delete()
        db.session.commit()
