"""Phase 4.5 reviewer assignments and evaluation periods."""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402
from extensions import db  # noqa: E402
from models import FacultyProfile, User  # noqa: E402
from models.evaluation_period import EvaluationPeriod  # noqa: E402
from models.reviewer_assignment import ReviewerAssignment  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402


def _faculty_id(app) -> int:
    with app.app_context():
        profile = FacultyProfile.query.join(User).filter(User.email == "faculty@facultylink.edu").first()
        assert profile
        return profile.faculty_id


def _reviewer_id(app) -> int:
    with app.app_context():
        user = User.query.filter_by(email="reviewer@facultylink.edu").first()
        assert user
        return user.user_id


def test_admin_assigns_and_reviewer_sees_faculty():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    reviewer_id = _reviewer_id(app)
    faculty_id = _faculty_id(app)
    csrf = _fetch_csrf(client)

    created = client.post(
        f"/api/v1/admin/reviewers/{reviewer_id}/assignments",
        json={"faculty_ids": [faculty_id]},
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201, created.get_json()
    assignment_id = created.get_json()["assignments"][0]["assignment_id"]

    reviewer = app.test_client()
    res = _login(reviewer, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(reviewer, res)
    listed = reviewer.get("/api/v1/reviewer/assigned-faculty")
    assert listed.status_code == 200
    assert any(row["faculty_id"] == faculty_id for row in listed.get_json()["faculty"])

    other = app.test_client()
    res = _login(other, "admin@facultylink.edu", "demo-admin")
    _persist_web_cookie(other, res)
    forbidden = other.get(f"/api/v1/reviewer/assigned-faculty/{faculty_id}")
    assert forbidden.status_code == 403

    csrf = _fetch_csrf(client)
    dup = client.post(
        f"/api/v1/admin/reviewers/{reviewer_id}/assignments",
        json={"faculty_ids": [faculty_id]},
        headers={"X-CSRF-Token": csrf},
    )
    assert dup.status_code == 201
    assert faculty_id in dup.get_json()["skipped"]

    csrf = _fetch_csrf(client)
    removed = client.patch(
        f"/api/v1/admin/reviewer-assignments/{assignment_id}",
        json={"is_active": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert removed.status_code == 200
    assert reviewer.get("/api/v1/reviewer/assigned-faculty").get_json()["faculty"] == []


def test_evaluation_period_crud_and_reviewer_read():
    app = create_app(TestConfig)
    client = app.test_client()
    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    now = datetime.now(timezone.utc)
    payload = {
        "name": f"Test Period {uuid.uuid4().hex[:6]}",
        "academicYear": "2025-2026",
        "semester": "Second Semester",
        "opensAt": (now + timedelta(days=2)).strftime("%Y-%m-%dT08:00:00+08:00"),
        "closesAt": (now + timedelta(days=20)).strftime("%Y-%m-%dT08:00:00+08:00"),
        "submissionEnabled": True,
        "reviewEnabled": False,
        "description": "Phase 4.5 test window",
        "acknowledgeOverlap": True,
    }
    created = client.post(
        "/api/v1/admin/evaluation-periods",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201, created.get_json()
    period_id = created.get_json()["period"]["period_id"]

    csrf = _fetch_csrf(client)
    bad = client.post(
        "/api/v1/admin/evaluation-periods",
        json={
            "name": "Bad",
            "academicYear": "2025-2026",
            "semester": "X",
            "opensAt": payload["closesAt"],
            "closesAt": payload["opensAt"],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert bad.status_code == 400

    reviewer = app.test_client()
    res = _login(reviewer, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(reviewer, res)
    admin_list = client.get("/api/v1/evaluation-periods")
    assert admin_list.status_code == 200
    periods = reviewer.get("/api/v1/evaluation-periods")
    assert periods.status_code == 200
    admin_periods = admin_list.get_json()["periods"]
    reviewer_periods = periods.get_json()["periods"]
    assert admin_periods == reviewer_periods
    assert any(p["period_id"] == period_id for p in reviewer_periods)

    csrf = _fetch_csrf(client)
    updated = client.patch(
        f"/api/v1/admin/evaluation-periods/{period_id}",
        json={"reviewEnabled": True, "acknowledgeOverlap": True},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.get_json()["period"]["reviewEnabled"] is True

    admin_list2 = client.get("/api/v1/evaluation-periods").get_json()["periods"]
    reviewer_list2 = reviewer.get("/api/v1/evaluation-periods").get_json()["periods"]
    assert admin_list2 == reviewer_list2
    row = next(p for p in reviewer_list2 if p["period_id"] == period_id)
    assert row["timezone"] == "Asia/Manila"
    assert row["reviewEnabled"] is True
    assert row["name"] == payload["name"]

    with app.app_context():
        db.session.query(EvaluationPeriod).filter_by(period_id=period_id).delete()
        db.session.commit()


def test_reviewer_cannot_mutate_assignments_or_periods():
    app = create_app(TestConfig)
    client = app.test_client()
    res = _login(client, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(client, res)
    csrf = _fetch_csrf(client)
    assert client.post("/api/v1/admin/evaluation-periods", json={}, headers={"X-CSRF-Token": csrf}).status_code == 403
    assert client.patch("/api/v1/admin/evaluation-periods/1", json={}, headers={"X-CSRF-Token": csrf}).status_code == 403
    assert client.post("/api/v1/admin/evaluation-periods/1/close-early", json={}, headers={"X-CSRF-Token": csrf}).status_code == 403
    assert (
        client.post("/api/v1/admin/reviewers/1/assignments", json={"faculty_ids": [1]}, headers={"X-CSRF-Token": csrf}).status_code
        == 403
    )
