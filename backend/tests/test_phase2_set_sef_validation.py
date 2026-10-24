"""Phase 2 SET/SEF OCR and rule-based validation (facultylink_test_db)."""
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
from models.evaluation_period import EvaluationPeriod  # noqa: E402
from models.user import User  # noqa: E402
from services.ocr.text_extractor import OcrExtractionResult  # noqa: E402
from services.validation.set_sef_engine import validate_set_sef_document  # noqa: E402
from tests.helpers_kra_i_a import seed_kra_i_criterion_a_set_sef  # noqa: E402
from tests.test_auth_api import _login  # noqa: E402
from tests.test_config import IsolatedTestConfig  # noqa: E402


SET_TEXT = """
Student Evaluation of Teachers (SET)
Faculty: Demo Faculty
Academic Year: 2025-2026
Semester: First Semester
Overall SET Rating: 88
"""

SEF_TEXT = """
Supervisor's Evaluation of Faculty (SEF)
Faculty: Demo Faculty
Academic Year: 2025-2026
Semester: First Semester
Overall SEF Rating: 91
"""

SCANNED_EMPTY = ""


def _open_period(app) -> int:
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        now = datetime.now(timezone.utc)
        period = EvaluationPeriod(
            period_code=f"p2-{uuid.uuid4().hex[:8]}",
            name="Phase 2 test window",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=14),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.commit()
        return period.period_id, criterion_id


def _mock_ocr(text: str, confidence: float = 90.0):
    def _fake(data, mime_type):  # noqa: ARG001
        status = "completed" if text else "completed"
        return OcrExtractionResult(text, confidence, "test_mock", status)

    return _fake


def test_engine_classifies_set_and_needs_verification_or_passed_without_credit():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, set_id, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        period = EvaluationPeriod(
            period_code=f"eng-{uuid.uuid4().hex[:6]}",
            name="Engine test",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closes_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            period_id=None,
            title="t",
            original_filename="t.pdf",
            storage_key="test/key",
            status="uploaded",
        )
        db.session.add_all([period, doc])
        db.session.flush()
        doc.period_id = period.period_id

        outcome = validate_set_sef_document(
            document=doc,
            period=period,
            faculty_user=user,
            ocr_text=SET_TEXT,
            ocr_confidence=90.0,
        )
        assert outcome.classified_indicator_code == "A.1"
        assert outcome.classified_indicator_id == set_id
        assert outcome.result in ("passed", "needs_verification")
        assert any(c.name == "authenticity_notice" for c in outcome.checks)


def test_engine_identity_mismatch():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        period = EvaluationPeriod(
            period_code=f"id-{uuid.uuid4().hex[:6]}",
            name="Id test",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closes_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        text = SET_TEXT.replace("Demo Faculty", "Wrong Person")
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            title="t",
            original_filename="t.pdf",
            storage_key="test/key2",
            status="uploaded",
        )
        db.session.add_all([period, doc])
        db.session.flush()
        outcome = validate_set_sef_document(
            document=doc,
            period=period,
            faculty_user=user,
            ocr_text=text,
            ocr_confidence=88.0,
        )
        assert outcome.result == "needs_verification"
        assert any(c.name == "faculty_identity" and not c.passed for c in outcome.checks)


def test_engine_invalid_rating():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        period = EvaluationPeriod(
            period_code=f"rt-{uuid.uuid4().hex[:6]}",
            name="Rating test",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closes_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        text = SET_TEXT.replace("Overall SET Rating: 88", "Overall SET Rating: 150")
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            title="t",
            original_filename="t.pdf",
            storage_key="test/key3",
            status="uploaded",
        )
        db.session.add_all([period, doc])
        db.session.flush()
        outcome = validate_set_sef_document(
            document=doc,
            period=period,
            faculty_user=user,
            ocr_text=text,
            ocr_confidence=88.0,
        )
        assert outcome.result == "needs_verification"
        assert any(c.name == "rating_range" and not c.passed for c in outcome.checks)


def test_engine_missing_required_fields():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        period = EvaluationPeriod(
            period_code=f"miss-{uuid.uuid4().hex[:6]}",
            name="Missing fields",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closes_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        text = "Student Evaluation of Teachers\nFaculty: Demo Faculty\n"
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            title="t",
            original_filename="t.pdf",
            storage_key="test/missing",
            status="uploaded",
        )
        db.session.add_all([period, doc])
        db.session.flush()
        outcome = validate_set_sef_document(
            document=doc,
            period=period,
            faculty_user=user,
            ocr_text=text,
            ocr_confidence=85.0,
            ocr_method="pypdf_text",
        )
        assert outcome.result == "needs_verification"
        assert any(c.name.startswith("required_") and not c.passed for c in outcome.checks)


def test_engine_low_ocr_confidence_not_trusted():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            title="t",
            original_filename="t.pdf",
            storage_key="test/lowocr",
            status="uploaded",
        )
        db.session.add(doc)
        db.session.flush()
        outcome = validate_set_sef_document(
            document=doc,
            period=None,
            faculty_user=user,
            ocr_text=SET_TEXT,
            ocr_confidence=20.0,
            ocr_method="pdf_tesseract",
        )
        assert outcome.result == "needs_verification"
        assert any(c.name == "ocr_confidence_threshold" and not c.passed for c in outcome.checks)


def test_engine_scanned_pdf_insufficient_text():
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        doc = Document(
            faculty_id=user.faculty_profile.faculty_id,
            criterion_id=criterion_id,
            title="t",
            original_filename="scan.pdf",
            storage_key="test/scan",
            status="uploaded",
        )
        db.session.add(doc)
        db.session.flush()
        outcome = validate_set_sef_document(
            document=doc,
            period=None,
            faculty_user=user,
            ocr_text=SCANNED_EMPTY,
            ocr_confidence=12.0,
        )
        assert outcome.result == "needs_verification"
        assert any(c.name == "ocr_sufficient_text" and not c.passed for c in outcome.checks)


@patch("services.document_pipeline.extract_text_from_bytes")
def test_upload_pipeline_set_document(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    period_id, criterion_id = _open_period(app)
    mock_extract.side_effect = _mock_ocr(SET_TEXT)

    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    pdf = b"%PDF-1.4\n" + SET_TEXT.encode() + uuid.uuid4().bytes
    res = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(pdf), "set-report.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.get_json()
    body = res.get_json()["document"]
    assert body["status"] in ("system_approved", "needs_verification")
    assert body.get("indicatorId") is not None

    detail = client.get(
        f"/api/v1/faculty/documents/{body['documentId']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200
    doc = detail.get_json()["document"]
    assert doc["validation"]["result"] in ("passed", "needs_verification")
    assert "checks" in doc["validation"]
    assert doc["extraction"]["extractedFields"].get("classified_indicator_code") == "A.1"


@patch("services.document_pipeline.extract_text_from_bytes")
def test_upload_classifies_sef(mock_extract):
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    period_id, criterion_id = _open_period(app)
    mock_extract.side_effect = _mock_ocr(SEF_TEXT)

    login = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    token = login.get_json()["access_token"]
    res = client.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(b"%PDF-1.4\n" + uuid.uuid4().bytes), "sef.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    doc = res.get_json()["document"]
    assert doc["status"] in ("system_approved", "needs_verification")
