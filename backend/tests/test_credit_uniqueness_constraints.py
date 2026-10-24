"""DB credit slot uniqueness (indicator-scoped, isolated test DB)."""
from __future__ import annotations

import hashlib
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.document import Document  # noqa: E402
from models.document_score_contribution import DocumentScoreContribution  # noqa: E402
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator  # noqa: E402
from models.faculty_profile import FacultyProfile  # noqa: E402
from models import User  # noqa: E402
from services.credit_uniqueness import (  # noqa: E402
    ONE_ACTIVE_CREDIT_PER_TERM,
    PER_EVIDENCE_HASH,
    build_credit_uniqueness_key,
)
from tests.test_config import IsolatedTestConfig  # noqa: E402


def _seed_set_indicator(app) -> tuple[int, int, int]:
    with app.app_context():
        faculty = (
            db.session.query(FacultyProfile)
            .join(User)
            .filter(User.email == "faculty@facultylink.edu")
            .first()
        )
        suffix = uuid.uuid4().hex[:8]
        kra = KraConfiguration(
            kra_code=f"KRA-I-{suffix}",
            kra_name="Instruction",
            guideline_version="test",
            is_active=True,
        )
        criterion = KraCriterion(
            kra=kra,
            criterion_code="A",
            criterion_name="Teaching Effectiveness",
            display_order=1,
        )
        indicator = KraIndicator(
            criterion=criterion,
            indicator_code="A.1",
            indicator_name="Student Evaluation (SET)",
            credit_uniqueness=ONE_ACTIVE_CREDIT_PER_TERM,
            display_order=1,
        )
        db.session.add_all([kra, criterion, indicator])
        db.session.commit()
        return faculty.faculty_id, criterion.criterion_id, indicator.indicator_id


def _random_sha() -> str:
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def _insert_doc(faculty_id: int, criterion_id: int, sha: str) -> Document:
    doc = Document(
        faculty_id=faculty_id,
        criterion_id=criterion_id,
        title="evidence",
        original_filename="f.pdf",
        storage_key=f"test/{uuid.uuid4().hex}",
        sha256_hash=sha,
        status="uploaded",
    )
    db.session.add(doc)
    db.session.flush()
    return doc


def test_one_active_credit_per_term_blocks_different_hashes():
    app = create_app(IsolatedTestConfig)
    faculty_id, criterion_id, indicator_id = _seed_set_indicator(app)
    ay, sem = "2025-2026", "First Semester"
    key = build_credit_uniqueness_key(
        mode=ONE_ACTIVE_CREDIT_PER_TERM,
        faculty_id=faculty_id,
        indicator_id=indicator_id,
        academic_year=ay,
        semester=sem,
        evidence_sha256=None,
    )
    with app.app_context():
        doc1 = _insert_doc(faculty_id, criterion_id, _random_sha())
        doc2 = _insert_doc(faculty_id, criterion_id, _random_sha())
        db.session.add(
            DocumentScoreContribution(
                document_id=doc1.document_id,
                faculty_id=faculty_id,
                indicator_id=indicator_id,
                academic_year=ay,
                semester=sem,
                evidence_sha256=doc1.sha256_hash,
                credit_uniqueness_mode=ONE_ACTIVE_CREDIT_PER_TERM,
                credit_uniqueness_key=key,
                credited_points=5,
                credit_state="credited",
            )
        )
        db.session.commit()
        db.session.add(
            DocumentScoreContribution(
                document_id=doc2.document_id,
                faculty_id=faculty_id,
                indicator_id=indicator_id,
                academic_year=ay,
                semester=sem,
                evidence_sha256=doc2.sha256_hash,
                credit_uniqueness_mode=ONE_ACTIVE_CREDIT_PER_TERM,
                credit_uniqueness_key=key,
                credited_points=3,
                credit_state="credited",
            )
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_per_evidence_allows_two_hashes_same_indicator():
    app = create_app(IsolatedTestConfig)
    faculty_id, criterion_id, indicator_id = _seed_set_indicator(app)
    ay, sem = "2025-2026", "First Semester"
    with app.app_context():
        db.session.query(KraIndicator).filter_by(indicator_id=indicator_id).update(
            {"credit_uniqueness": PER_EVIDENCE_HASH}
        )
        doc1 = _insert_doc(faculty_id, criterion_id, _random_sha())
        doc2 = _insert_doc(faculty_id, criterion_id, _random_sha())
        for doc, points in ((doc1, 4), (doc2, 6)):
            db.session.add(
                DocumentScoreContribution(
                    document_id=doc.document_id,
                    faculty_id=faculty_id,
                    indicator_id=indicator_id,
                    academic_year=ay,
                    semester=sem,
                    evidence_sha256=doc.sha256_hash,
                    credit_uniqueness_mode=PER_EVIDENCE_HASH,
                    credit_uniqueness_key=build_credit_uniqueness_key(
                        mode=PER_EVIDENCE_HASH,
                        faculty_id=faculty_id,
                        indicator_id=indicator_id,
                        academic_year=ay,
                        semester=sem,
                        evidence_sha256=doc.sha256_hash,
                    ),
                    credited_points=points,
                    credit_state="credited",
                )
            )
        db.session.commit()
        count = (
            db.session.query(DocumentScoreContribution)
            .filter_by(
                faculty_id=faculty_id,
                indicator_id=indicator_id,
                credit_state="credited",
            )
            .count()
        )
        assert count == 2


def test_revoked_row_does_not_block_new_credit_version():
    app = create_app(IsolatedTestConfig)
    faculty_id, criterion_id, indicator_id = _seed_set_indicator(app)
    ay, sem = "2025-2026", "First Semester"
    key = build_credit_uniqueness_key(
        mode=ONE_ACTIVE_CREDIT_PER_TERM,
        faculty_id=faculty_id,
        indicator_id=indicator_id,
        academic_year=ay,
        semester=sem,
        evidence_sha256=None,
    )
    with app.app_context():
        doc1 = _insert_doc(faculty_id, criterion_id, _random_sha())
        first = DocumentScoreContribution(
            document_id=doc1.document_id,
            faculty_id=faculty_id,
            indicator_id=indicator_id,
            academic_year=ay,
            semester=sem,
            evidence_sha256=doc1.sha256_hash,
            credit_uniqueness_mode=ONE_ACTIVE_CREDIT_PER_TERM,
            credit_uniqueness_key=key,
            credited_points=5,
            credit_state="credited",
            version_no=1,
        )
        db.session.add(first)
        db.session.commit()
        first_id = first.contribution_id
        db.session.query(DocumentScoreContribution).filter_by(contribution_id=first_id).update(
            {"credit_state": "revoked", "revoke_reason": "reviewer correction"}
        )
        db.session.commit()
        doc2 = _insert_doc(faculty_id, criterion_id, _random_sha())
        db.session.add(
            DocumentScoreContribution(
                document_id=doc2.document_id,
                faculty_id=faculty_id,
                indicator_id=indicator_id,
                academic_year=ay,
                semester=sem,
                evidence_sha256=doc2.sha256_hash,
                credit_uniqueness_mode=ONE_ACTIVE_CREDIT_PER_TERM,
                credit_uniqueness_key=key,
                credited_points=7,
                credit_state="credited",
                version_no=2,
                supersedes_contribution_id=first_id,
            )
        )
        db.session.commit()
        active = (
            db.session.query(DocumentScoreContribution)
            .filter_by(credit_state="credited", credit_uniqueness_key=key)
            .count()
        )
        assert active == 1
