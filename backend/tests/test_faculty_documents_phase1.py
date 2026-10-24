"""Phase 1 faculty document upload API (isolated test DB)."""
from __future__ import annotations

import io
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.evaluation_period import EvaluationPeriod  # noqa: E402
from models.kra_configuration import KraConfiguration, KraCriterion  # noqa: E402
from tests.test_auth_api import _login  # noqa: E402
from tests.test_config import IsolatedTestConfig  # noqa: E402


def _seed_criterion(app) -> int:
    with app.app_context():
        existing = db.session.query(KraCriterion).order_by(KraCriterion.criterion_id).first()
        if existing:
            return existing.criterion_id
        kra = KraConfiguration(
            kra_code="KRA I",
            kra_name="Instruction",
            guideline_version="phase1-test",
            is_active=True,
        )
        criterion = KraCriterion(
            kra=kra,
            criterion_code="A",
            criterion_name="Teaching",
            display_order=1,
        )
        db.session.add_all([kra, criterion])
        db.session.commit()
        return criterion.criterion_id


def _faculty_bearer(client):
    res = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    assert res.status_code == 200, res.get_json()
    return res.get_json()["access_token"]


def _open_period(app) -> tuple[int, int]:
    criterion_id = _seed_criterion(app)
    code = f"test-upload-{uuid.uuid4().hex[:10]}"
    with app.app_context():
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=code,
            name="Test Upload Window",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=30),
            submission_enabled=True,
            review_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        return period.period_id, criterion_id


def test_upload_rejected_when_period_closed():
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    token = _faculty_bearer(client)
    criterion_id = _seed_criterion(app)
    with app.app_context():
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"test-closed-{uuid.uuid4().hex[:10]}",
            name="Closed",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=now - timedelta(days=10),
            closes_at=now - timedelta(hours=1),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id

    data = {
        "period_id": str(period_id),
        "criterion_id": str(criterion_id),
        "title": "Sample",
    }
    res = client.post(
        "/api/v1/faculty/documents",
        data={**data, "file": (io.BytesIO(b"%PDF-1.4 test"), "sample.pdf")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.get_json()["error"] == "submission_closed"


def test_upload_success_stays_uploaded():
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    token = _faculty_bearer(client)
    period_id, criterion_id = _open_period(app)

    payload = f"%PDF-1.4 faculty phase1 upload {uuid.uuid4()}".encode()
    res = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "title": "Teaching Portfolio",
            "file": (io.BytesIO(payload), "portfolio.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.get_json()
    body = res.get_json()["document"]
    assert body["status"] == "needs_verification"
    assert body["periodId"] == period_id
    assert body["sha256Hash"]

    listed = client.get(
        "/api/v1/faculty/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert any(d["documentId"] == body["documentId"] for d in listed.get_json()["documents"])


def test_duplicate_upload_conflict():
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    token = _faculty_bearer(client)
    period_id, criterion_id = _open_period(app)
    payload = f"%PDF-1.4 duplicate test {uuid.uuid4()}".encode()

    def post():
        return client.post(
            "/api/v1/faculty/documents",
            data={
                "period_id": str(period_id),
                "criterion_id": str(criterion_id),
                "file": (io.BytesIO(payload), "dup.pdf"),
            },
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert post().status_code == 201
    dup = post()
    assert dup.status_code == 409
    assert dup.get_json()["error"] == "duplicate_evidence"
