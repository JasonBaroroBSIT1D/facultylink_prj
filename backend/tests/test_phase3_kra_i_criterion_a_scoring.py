"""Phase 3 — KRA I Criterion A scoring, system approval, and configuration snapshots."""
from __future__ import annotations

import io
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.document import Document  # noqa: E402
from models.document_score_contribution import DocumentScoreContribution  # noqa: E402
from models.evaluation_period import EvaluationPeriod  # noqa: E402
from models.kra_configuration import KraIndicator, ScoringRule  # noqa: E402
from models.user import User  # noqa: E402
from services.document_pipeline import process_criterion_a_set_sef  # noqa: E402
from services.kra_i_criterion_a_scoring import calculate_points_from_rule  # noqa: E402
from tests.helpers_kra_i_a import seed_kra_i_criterion_a_set_sef  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import IsolatedTestConfig  # noqa: E402
from tests.test_kra_configuration_api import _clear_kra_tables  # noqa: E402
from tests.test_kra_i_criterion_a_metadata_editing import _seed_kra_i_criterion_a  # noqa: E402
from tests.test_phase2_set_sef_validation import SET_TEXT, _mock_ocr  # noqa: E402


def _unique_set_text():
    start = 2040 + (int(uuid.uuid4().hex[:2], 16) % 50)
    year = f"{start}-{start + 1}"
    return SET_TEXT.replace("2025-2026", year), year


def test_calculate_points_uses_saved_max():
    points = calculate_points_from_rule(rating=88.0, rule_config={"max_points": 36, "formula": "(rating / 100) * max_points"})
    assert points == 31.68


@patch("services.document_pipeline.extract_text_from_bytes")
def test_valid_set_upload_system_approved_and_credited(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    text, academic_year = _unique_set_text()
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"p3-{uuid.uuid4().hex[:8]}",
            name="Phase 3",
            academic_year=academic_year,
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=7),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id

    mock_extract.side_effect = _mock_ocr(text)
    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    res = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(b"%PDF-1.4\n" + text.encode()), "set-report.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.get_json()
    doc_id = res.get_json()["document"]["documentId"]
    assert res.get_json()["document"]["status"] == "system_approved"

    with app.app_context():
        contrib = DocumentScoreContribution.query.filter_by(document_id=doc_id).one()
        assert float(contrib.credited_points) == 31.68
        assert contrib.credit_state == "credited"
        assert contrib.system_decision == "auto_approved"
        assert contrib.rule_snapshot.get("rule_config", {}).get("max_points") == 36


@patch("services.document_pipeline.extract_text_from_bytes")
def test_invalid_rating_needs_verification_zero_credit(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"p3b-{uuid.uuid4().hex[:8]}",
            name="Phase 3 invalid",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=7),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id

    bad_text = SET_TEXT.replace("Overall SET Rating: 88", "Overall SET Rating: 150")
    mock_extract.side_effect = _mock_ocr(bad_text)
    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    res = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(b"%PDF-1.4\n"), "set-bad.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    doc_id = res.get_json()["document"]["documentId"]
    assert res.get_json()["document"]["status"] == "needs_verification"
    with app.app_context():
        contrib = DocumentScoreContribution.query.filter_by(document_id=doc_id).one()
        assert float(contrib.credited_points) == 0.0
        assert contrib.credit_state == "none"


@patch("services.document_pipeline.extract_text_from_bytes")
def test_admin_scoring_change_does_not_rewrite_prior_contribution(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    text, academic_year = _unique_set_text()
    mock_extract.side_effect = _mock_ocr(text)
    with app.app_context():
        _clear_kra_tables()
        criterion_id, set_id, _, set_rule_id = _seed_kra_i_criterion_a()
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"snap-{uuid.uuid4().hex[:6]}",
            name="Snap",
            academic_year=academic_year,
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=3),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id
    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    upload = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(b"%PDF-1.4\n" + text.encode()), "snap-set.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    doc_id = upload.get_json()["document"]["documentId"]

    with app.app_context():
        old_contrib = DocumentScoreContribution.query.filter_by(document_id=doc_id).one()
        old_snapshot_max = old_contrib.rule_snapshot["rule_config"]["max_points"]

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    client.patch(
        "/api/v1/admin/kra-configuration/kra-i/criterion-a",
        json={"scoring_rules": [{"rule_id": set_rule_id, "max_points": 20}]},
        headers={"X-CSRF-Token": csrf},
    )

    with app.app_context():
        refreshed = db.session.get(DocumentScoreContribution, old_contrib.contribution_id)
        assert refreshed.rule_snapshot["rule_config"]["max_points"] == old_snapshot_max
        rule = db.session.get(ScoringRule, set_rule_id)
        assert float(rule.rule_config["max_points"]) == 20
        _clear_kra_tables()


@patch("services.document_pipeline.extract_text_from_bytes")
def test_duplicate_term_blocks_second_credit(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"dup-{uuid.uuid4().hex[:8]}",
            name="Dup",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=7),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.period_id

    mock_extract.side_effect = _mock_ocr(SET_TEXT)
    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    for _ in range(2):
        res = client.post(
            "/api/v1/faculty/documents",
            data={
                "period_id": str(period_id),
                "criterion_id": str(criterion_id),
                "file": (io.BytesIO(b"%PDF-1.4\n" + uuid.uuid4().bytes), "set-dup.pdf"),
            },
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201

    with app.app_context():
        credited = DocumentScoreContribution.query.filter_by(credit_state="credited").all()
        assert len(credited) == 1
        second = Document.query.order_by(Document.document_id.desc()).first()
        assert second.status == "needs_verification"
        second_contrib = DocumentScoreContribution.query.filter_by(document_id=second.document_id).one()
        assert float(second_contrib.credited_points) == 0.0
