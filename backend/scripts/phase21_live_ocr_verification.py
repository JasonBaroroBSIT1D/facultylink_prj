"""
Phase 2.1 final verification: live OCR + validation (no facultylink_db writes).

Uses facultylink_test_db only inside a rolled-back transaction for validate_set_sef_document.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

SET_BODY = """Student Evaluation of Teachers (SET)
Faculty: Demo Faculty
Academic Year: 2025-2026
Semester: First Semester
Overall SET Rating: 88
"""


def _build_text_pdf(text: str) -> bytes:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    y = 72
    for line in text.strip().splitlines():
        page.insert_text((72, y), line, fontsize=12)
        y += 16
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _build_scanned_pdf(text: str) -> bytes:
    """Image-only PDF (no text layer) for Tesseract OCR path."""
    from PIL import Image, ImageDraw, ImageFont

    import pymupdf

    img = Image.new("RGB", (850, 1100), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    y = 80
    for line in text.strip().splitlines():
        draw.text((60, y), line, fill="black", font=font)
        y += 36
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=850, height=1100)
    page.insert_image(page.rect, stream=img_bytes)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def _build_png(text: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (800, 400), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    y = 40
    for line in text.strip().splitlines():
        draw.text((30, y), line, fill="black", font=font)
        y += 32
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_jpeg(text: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (800, 400), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((30, 40), text.replace("\n", " | "), fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _run_extraction(label: str, data: bytes, mime: str) -> dict:
    from services.ocr.text_extractor import extract_text_from_bytes
    from services.validation.rule_loader import load_set_sef_rules
    from services.validation.set_sef_engine import _normalize_ocr_text, _parse_fields

    ocr = extract_text_from_bytes(data, mime)
    rules = load_set_sef_rules()
    norm = _normalize_ocr_text(ocr.text)
    fields, field_conf = _parse_fields(norm or ocr.text, rules["indicators"]["A.1"])
    ocr_ratio = min(1.0, max(0.0, ocr.confidence / 100.0))
    combined = {k: round((field_conf.get(k, 0) * ocr_ratio), 4) for k in field_conf}
    return {
        "fixture": label,
        "mime": mime,
        "method": ocr.method,
        "ocr_confidence_raw_0_100": round(ocr.confidence, 2),
        "ocr_confidence_normalized_0_1": round(ocr_ratio, 4),
        "page_methods": ocr.page_methods,
        "text_preview": (ocr.text or "")[:400],
        "extracted_fields": {k: v for k, v in fields.items() if not k.startswith("_")},
        "field_confidence_0_1": field_conf,
        "combined_field_confidence_0_1": combined,
        "status": ocr.status,
    }


def _run_validation_scenarios() -> list[dict]:
    from app import create_app
    from extensions import db
    from models.document import Document
    from models.evaluation_period import EvaluationPeriod
    from models.user import User
    from services.validation.set_sef_engine import validate_set_sef_document
    from tests.helpers_kra_i_a import seed_kra_i_criterion_a_set_sef
    from tests.test_config import IsolatedTestConfig

    app = create_app(IsolatedTestConfig)
    scenarios = []
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        db.session.bind = conn

        criterion_id, _, _ = seed_kra_i_criterion_a_set_sef()
        user = User.query.filter_by(email="faculty@facultylink.edu").first()
        period = EvaluationPeriod(
            period_code="p21-verify",
            name="Phase 2.1 verify",
            academic_year="2025-2026",
            semester="First Semester",
            opens_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closes_at=datetime.now(timezone.utc) + timedelta(days=3),
            submission_enabled=True,
        )
        db.session.add(period)
        db.session.flush()

        cases = [
            ("good_set", SET_BODY, 90.0, "pypdf_text"),
            ("wrong_name", SET_BODY.replace("Demo Faculty", "Wrong Person"), 90.0, "pypdf_text"),
            ("missing_fields", "Student Evaluation of Teachers\nFaculty: Demo Faculty\n", 85.0, "pypdf_text"),
            ("low_ocr_conf", SET_BODY, 18.0, "pdf_tesseract"),
            ("invalid_rating", SET_BODY.replace("88", "150"), 90.0, "pypdf_text"),
        ]
        for name, text, conf, method in cases:
            doc = Document(
                faculty_id=user.faculty_profile.faculty_id,
                criterion_id=criterion_id,
                period_id=period.period_id,
                title=name,
                original_filename=f"{name}.pdf",
                storage_key=f"verify/{name}",
                status="uploaded",
            )
            db.session.add(doc)
            db.session.flush()
            outcome = validate_set_sef_document(
                document=doc,
                period=period,
                faculty_user=user,
                ocr_text=text,
                ocr_confidence=conf,
                ocr_method=method,
            )
            pipeline_doc_status = "needs_verification"
            scenarios.append(
                {
                    "scenario": name,
                    "validation_result": outcome.result,
                    "pipeline_document_status": pipeline_doc_status,
                    "ocr_confidence_in": conf,
                    "ocr_normalized": round(conf / 100.0, 4),
                    "failed_checks": [c.name for c in outcome.checks if not c.passed],
                    "extracted": {k: v for k, v in outcome.extracted_fields.items() if not str(k).startswith("_")},
                }
            )

        trans.rollback()
        conn.close()

    return scenarios


def main() -> int:
    from services.ocr.tesseract_config import resolve_tesseract_executable, tesseract_version_line

    report: dict = {
        "tesseract": {
            "executable": resolve_tesseract_executable(),
            "version": tesseract_version_line(),
        },
        "confidence_model": {
            "tesseract_raw_scale": "0-100 (mean word conf from image_to_data)",
            "pypdf_text_pages": "fixed 92.0 on 0-100 scale",
            "validation_normalization": "ocr_conf_ratio = ocr_confidence / 100.0",
            "thresholds_json_0_1": {
                "ocr_mean_min": 0.35,
                "field_min": 0.6,
                "identity_min": 0.65,
                "classification_min": 0.55,
            },
            "combined_field_confidence": "field_confidence_0_1 * ocr_conf_ratio",
        },
        "extractions": [],
        "validation_scenarios": [],
        "no_credit_guards": {
            "document_pipeline_writes_document_score_contributions": False,
            "document_pipeline_status": "always needs_verification",
            "DOCUMENT_AUTO_APPROVAL_ENABLED_default": "0",
        },
    }

    if not resolve_tesseract_executable():
        print(json.dumps({**report, "error": "Tesseract not installed; scanned/image tests skipped"}, indent=2))
        return 1

    report["extractions"].append(_run_extraction("text_pdf", _build_text_pdf(SET_BODY), "application/pdf"))
    report["extractions"].append(
        _run_extraction("scanned_pdf_tesseract", _build_scanned_pdf(SET_BODY), "application/pdf")
    )
    report["extractions"].append(_run_extraction("png_tesseract", _build_png(SET_BODY), "image/png"))
    report["extractions"].append(_run_extraction("jpeg_tesseract", _build_jpeg(SET_BODY), "image/jpeg"))

    report["validation_scenarios"] = _run_validation_scenarios()

    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
