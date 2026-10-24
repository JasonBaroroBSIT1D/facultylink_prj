"""Post-KRA import faculty upload verification on facultylink_db."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

if os.getenv("DB_NAME") != "facultylink_db":
    raise SystemExit("Refusing: DB_NAME must be facultylink_db")


def main() -> int:
    from app import create_app
    from config import Config
    from extensions import db
    from models.document import Document
    from services.document_storage import absolute_path_for_key

    app = create_app(Config)
    fac = app.test_client()
    report: dict = {"tests": {}, "created": []}

    login = fac.post(
        "/api/v1/auth/login",
        json={"email": "faculty@facultylink.edu", "password": "demo-faculty", "client": "mobile"},
    )
    report["faculty_login"] = login.status_code
    if login.status_code != 200:
        print(json.dumps(report, indent=2))
        return 1
    token = login.get_json()["access_token"]

    with app.app_context():
        from models.faculty_profile import FacultyProfile
        from models import User

        profile = (
            db.session.query(FacultyProfile)
            .join(User)
            .filter(User.email == "faculty@facultylink.edu")
            .first()
        )
        faculty_id = profile.faculty_id
        from models.kra_configuration import KraCriterion

        from models.kra_configuration import KraConfiguration

        criterion = (
            db.session.query(KraCriterion)
            .join(KraConfiguration, KraConfiguration.kra_id == KraCriterion.kra_id)
            .filter(KraConfiguration.kra_code == "KRA I", KraCriterion.criterion_code == "A")
            .first()
        )
        criterion_id = criterion.criterion_id

    open_period_id = 24
    closed_period_id = 25
    pdf = f"%PDF-1.4\nFacultyLink post-KRA upload {uuid.uuid4()}\n".encode()
    pdf_hash = hashlib.sha256(pdf).hexdigest()

    upload = fac.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(open_period_id),
            "criterion_id": str(criterion_id),
            "title": "SET evidence test upload",
            "file": (io.BytesIO(pdf), "post-kra-upload-test.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    report["tests"]["upload_open"] = {"status": upload.status_code, "body": upload.get_json()}

    if upload.status_code == 201:
        doc_json = upload.get_json()["document"]
        doc_id = doc_json["documentId"]
        report["created"].append({"document_id": doc_id, "title": doc_json["title"]})
        with app.app_context():
            row = db.session.get(Document, doc_id)
            path = absolute_path_for_key(row.storage_key)
            report["tests"]["db_verification"] = {
                "document_id": row.document_id,
                "faculty_id": row.faculty_id,
                "expected_faculty_id": faculty_id,
                "period_id": row.period_id,
                "expected_period_id": open_period_id,
                "criterion_id": row.criterion_id,
                "expected_criterion_id": criterion_id,
                "sha256_hash": row.sha256_hash,
                "expected_sha256": pdf_hash,
                "status": row.status,
                "storage_key": row.storage_key,
                "storage_path": str(path),
                "file_exists": path.is_file(),
                "file_size_bytes": row.file_size_bytes,
            }

        dup = fac.post(
            "/api/v1/faculty/documents",
            data={
                "period_id": str(open_period_id),
                "criterion_id": str(criterion_id),
                "file": (io.BytesIO(pdf), "post-kra-dup.pdf"),
            },
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )
        report["tests"]["duplicate_upload"] = {"status": dup.status_code, "body": dup.get_json()}

    closed = app.test_client()
    cl = closed.post(
        "/api/v1/faculty/documents",
        data={
            "period_id": str(closed_period_id),
            "criterion_id": str(criterion_id),
            "file": (io.BytesIO(pdf), "closed-test.pdf"),
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    report["tests"]["closed_period_upload"] = {"status": cl.status_code, "body": cl.get_json()}

    print(json.dumps(report, indent=2))
    ok = (
        report["tests"].get("upload_open", {}).get("status") == 201
        and report["tests"].get("duplicate_upload", {}).get("status") == 409
        and report["tests"].get("closed_period_upload", {}).get("status") == 403
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
