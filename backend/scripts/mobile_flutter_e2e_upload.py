"""Simulate Flutter mobile client: login → periods → kra config → upload → detail."""
from __future__ import annotations

import io
import json
import sys
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

BASE = "http://127.0.0.1:5000"

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


def main() -> int:
    session = requests.Session()
    login = session.post(
        f"{BASE}/api/v1/auth/login",
        json={"email": "faculty@facultylink.edu", "password": "demo-faculty", "client": "mobile"},
        timeout=30,
    )
    if login.status_code != 200:
        print("LOGIN FAILED", login.status_code, login.text)
        return 1
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    print("LOGIN", login.status_code)

    health = session.get(f"{BASE}/api/v1/health", timeout=15)
    print("HEALTH", health.status_code, json.dumps(health.json().get("documents_pipeline"), indent=2))

    periods = session.get(f"{BASE}/api/v1/evaluation-periods", headers=headers, timeout=30)
    kra = session.get(f"{BASE}/api/v1/kra-configuration", headers=headers, timeout=30)
    if periods.status_code != 200 or kra.status_code != 200:
        print("CONFIG FAILED", periods.status_code, kra.status_code)
        return 1

    period_rows = periods.json().get("periods") or []
    open_periods = [p for p in period_rows if p.get("status") == "Open" and p.get("submissionEnabled")]
    if not open_periods:
        print("NO OPEN PERIOD")
        return 1
    period = open_periods[0]
    period_id = period["period_id"]
    print("PERIOD", period_id, period.get("name"), period.get("academicYear"), period.get("semester"))

    criterion_id = None
    kra_i = None
    for k in kra.json().get("kras") or []:
        if k.get("code") == "KRA I":
            kra_i = k
            for c in k.get("criteria") or []:
                if c.get("code") == "A":
                    criterion_id = c["criterion_id"]
    if not criterion_id:
        print("KRA I CRITERION A NOT FOUND")
        return 1
    print("CRITERION_A_ID", criterion_id, "from KRA I", kra_i.get("kra_id"))

    pdf = _build_text_pdf(SET_BODY)
    name = f"mobile-e2e-set-{uuid.uuid4().hex[:8]}.pdf"
    files = {"file": (name, io.BytesIO(pdf), "application/pdf")}
    data = {
        "period_id": str(period_id),
        "criterion_id": str(criterion_id),
        "title": "Mobile E2E SET",
    }
    upload = session.post(
        f"{BASE}/api/v1/faculty/documents",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files,
        timeout=120,
    )
    print("UPLOAD", upload.status_code)
    if upload.status_code != 201:
        print(upload.text)
        return 1
    doc_id = upload.json()["document"]["documentId"]
    upload_doc = upload.json()["document"]
    print("UPLOAD_BODY_STATUS", upload_doc.get("status"), "indicatorId", upload_doc.get("indicatorId"))

    detail = session.get(f"{BASE}/api/v1/faculty/documents/{doc_id}", headers=headers, timeout=30)
    print("DETAIL", detail.status_code)
    payload = detail.json()["document"]
    extraction = payload.get("extraction") or {}
    validation = payload.get("validation") or {}
    fields = extraction.get("extractedFields") or {}
    checks = (validation.get("checks") or {}).get("items") or []

    report = {
        "documentId": doc_id,
        "status": payload.get("status"),
        "indicatorId": payload.get("indicatorId"),
        "extraction_status": extraction.get("status"),
        "extraction_method": extraction.get("extractionMethod"),
        "ocr_confidence": extraction.get("ocrConfidence"),
        "classified_indicator_code": fields.get("classified_indicator_code"),
        "extracted_faculty_name": fields.get("faculty_name"),
        "extracted_academic_year": fields.get("academic_year"),
        "extracted_semester": fields.get("semester"),
        "extracted_overall_rating": fields.get("overall_rating"),
        "validation_result": validation.get("result"),
        "validation_explanation": validation.get("explanation"),
        "rule_version": validation.get("ruleVersion"),
        "failed_checks": [c.get("name") for c in checks if not c.get("passed")],
        "check_count": len(checks),
    }
    print(json.dumps(report, indent=2, default=str))

    ok = True
    if payload.get("status") != "needs_verification":
        print("FAIL: expected needs_verification")
        ok = False
    if not extraction.get("extractionId") and extraction.get("extractionId") != 0:
        if extraction.get("extractionId") is None:
            print("FAIL: missing extraction record")
            ok = False
    if not validation.get("validationId") and validation.get("validationId") != 0:
        if validation.get("validationId") is None:
            print("FAIL: missing validation record")
            ok = False
    if fields.get("classified_indicator_code") != "A.1":
        print("WARN/FAIL: expected A.1 classification for SET sample")
        ok = False
    if fields.get("overall_rating") != 88.0 and fields.get("overall_rating") != 88:
        print("WARN/FAIL: expected overall_rating 88")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
