"""
Phase 1 live verification against facultylink_db (creates test evaluation periods only).
Does not import KRA rows or enable scoring/auto-approval.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

if os.getenv("DB_NAME") != "facultylink_db":
    raise SystemExit(f"Refusing to run: DB_NAME is {os.getenv('DB_NAME')!r}, expected facultylink_db")

MANILA = ZoneInfo("Asia/Manila")


def _manila_iso(dt: datetime) -> str:
    local = dt.astimezone(MANILA)
    return local.strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"


def _login(client, email: str, password: str, client_type: str = "web"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "client": client_type},
    )


def _cookie_token(client, response) -> str | None:
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("facultylink_access="):
            return header.split(";", 1)[0].split("=", 1)[1]
    return None


def _csrf(client, token: str) -> str:
    res = client.get("/api/v1/auth/csrf", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.get_json()
    csrf = res.get_json()["csrf_token"]
    client.set_cookie("facultylink_csrf", csrf, path="/")
    return csrf


def main() -> int:
    from app import create_app
    from config import Config
    from extensions import db
    from models.evaluation_period import EvaluationPeriod

    app = create_app(Config)
    client = app.test_client()
    report: dict = {"database": "facultylink_db", "test_records_created": [], "tests": {}}

    # --- Admin: create open + closed test periods ---
    admin = _login(client, "admin@facultylink.edu", "demo-admin")
    if admin.status_code != 200:
        report["tests"]["admin_login"] = {
            "status": admin.status_code,
            "body": admin.get_json(),
            "note": "admin login failed; cannot create periods via API",
        }
        print(json.dumps(report, indent=2))
        return 1

    admin_token = _cookie_token(client, admin) or admin.get_json().get("access_token")
    client.set_cookie("facultylink_access", admin_token, path="/")
    csrf = _csrf(client, admin_token)

    now = datetime.now(timezone.utc)
    open_code = f"phase1-open-{uuid.uuid4().hex[:8]}"
    closed_code = f"phase1-closed-{uuid.uuid4().hex[:8]}"
    open_body = {
        "name": "Phase 1 Upload Test (Open)",
        "academicYear": "2025-2026",
        "semester": "First Semester",
        "opensAt": _manila_iso(now - timedelta(hours=2)),
        "closesAt": _manila_iso(now + timedelta(days=60)),
        "submissionEnabled": True,
        "reviewEnabled": True,
        "period_code": open_code,
        "description": "Automated Phase 1 verification record — safe to delete later.",
    }
    closed_body = {
        "name": "Phase 1 Upload Test (Closed)",
        "academicYear": "2025-2026",
        "semester": "First Semester",
        "opensAt": _manila_iso(now - timedelta(days=30)),
        "closesAt": _manila_iso(now - timedelta(hours=1)),
        "submissionEnabled": True,
        "period_code": closed_code,
        "description": "Closed window for submission gate test.",
    }
    open_res = client.post(
        "/api/v1/admin/evaluation-periods",
        json=open_body,
        headers={"Authorization": f"Bearer {admin_token}", "X-CSRF-Token": csrf},
    )
    closed_res = client.post(
        "/api/v1/admin/evaluation-periods",
        json=closed_body,
        headers={"Authorization": f"Bearer {admin_token}", "X-CSRF-Token": csrf},
    )
    report["tests"]["create_open_period"] = {"status": open_res.status_code, "body": open_res.get_json()}
    report["tests"]["create_closed_period"] = {"status": closed_res.status_code, "body": closed_res.get_json()}

    open_period_id = None
    closed_period_id = None
    if open_res.status_code == 201:
        open_period_id = open_res.get_json()["period"]["period_id"]
        report["test_records_created"].append(
            {"type": "evaluation_period", "period_id": open_period_id, "period_code": open_code}
        )
    if closed_res.status_code == 201:
        closed_period_id = closed_res.get_json()["period"]["period_id"]
        report["test_records_created"].append(
            {"type": "evaluation_period", "period_id": closed_period_id, "period_code": closed_code}
        )

    # --- Faculty login (demo account) ---
    fac = _login(client, "faculty@facultylink.edu", "demo-faculty", "mobile")
    report["tests"]["faculty_login"] = {"status": fac.status_code}
    if fac.status_code != 200:
        report["tests"]["faculty_login"]["body"] = fac.get_json()
        print(json.dumps(report, indent=2))
        return 1
    fac_token = fac.get_json()["access_token"]

    pdf_bytes = b"%PDF-1.4\n% Phase1 verification minimal PDF\n"
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Closed period must reject before criterion check
    if closed_period_id:
        closed_upload = client.post(
            "/api/v1/faculty/documents",
            data={
                "period_id": str(closed_period_id),
                "criterion_id": "1",
                "title": "Closed gate test",
                "file": (io.BytesIO(pdf_bytes), "phase1-closed-test.pdf"),
            },
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {fac_token}"},
        )
        report["tests"]["upload_closed_period"] = {
            "status": closed_upload.status_code,
            "body": closed_upload.get_json(),
            "expected": "403 submission_closed",
        }

    # Open period: expect criterion missing (no KRA import)
    criterion_id = None
    with app.app_context():
        from models.kra_configuration import KraCriterion

        row = db.session.query(KraCriterion).order_by(KraCriterion.criterion_id).first()
        if row:
            criterion_id = row.criterion_id

    if open_period_id:
        upload = client.post(
            "/api/v1/faculty/documents",
            data={
                "period_id": str(open_period_id),
                "criterion_id": str(criterion_id or 999999),
                "title": "Phase 1 SET test upload",
                "file": (io.BytesIO(pdf_bytes), "phase1-upload-test.pdf"),
            },
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {fac_token}"},
        )
        report["tests"]["upload_open_period"] = {
            "status": upload.status_code,
            "body": upload.get_json(),
            "pdf_sha256": pdf_hash,
        }
        if upload.status_code == 201:
            doc = upload.get_json()["document"]
            report["tests"]["upload_open_period"]["document"] = doc
            with app.app_context():
                from models.document import Document
                from services.document_storage import absolute_path_for_key

                row = db.session.get(Document, doc["documentId"])
                storage_path = str(absolute_path_for_key(row.storage_key)) if row else None
                report["tests"]["upload_db_verification"] = {
                    "document_id": row.document_id if row else None,
                    "period_id": row.period_id,
                    "faculty_id": row.faculty_id,
                    "criterion_id": row.criterion_id,
                    "sha256_hash": row.sha256_hash,
                    "storage_key": row.storage_key,
                    "storage_path": storage_path,
                    "status": row.status,
                    "file_exists": Path(storage_path).is_file() if storage_path else False,
                }
            dup = client.post(
                "/api/v1/faculty/documents",
                data={
                    "period_id": str(open_period_id),
                    "criterion_id": str(criterion_id or 999999),
                    "file": (io.BytesIO(pdf_bytes), "phase1-upload-test-dup.pdf"),
                },
                content_type="multipart/form-data",
                headers={"Authorization": f"Bearer {fac_token}"},
            )
            report["tests"]["duplicate_upload"] = {"status": dup.status_code, "body": dup.get_json()}
        else:
            report["blockers"] = report.get("blockers", []) + [
                "End-to-end upload blocked: no kra_criteria row on facultylink_db (KRA import not approved)."
                if not criterion_id
                else f"Upload failed with HTTP {upload.status_code}"
            ]

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
