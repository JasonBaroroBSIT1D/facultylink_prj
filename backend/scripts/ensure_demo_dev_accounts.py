"""Restore development demo faculty/reviewer accounts if missing (non-destructive)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from werkzeug.security import generate_password_hash

from app import create_app
from config import Config
from extensions import db
from models import User
from models.faculty_profile import FacultyProfile

DEMO_ACCOUNTS = (
    ("reviewer@facultylink.edu", "demo-reviewer", "reviewer", "Faculty Reviewer"),
    ("faculty@facultylink.edu", "demo-faculty", "faculty", "Demo Faculty"),
)


def ensure() -> int:
    if os.getenv("FACULTYLINK_PYTEST_ACTIVE") == "1":
        raise SystemExit(
            "ensure_demo_dev_accounts.py must not run during pytest. "
            "Demo accounts for tests are seeded via backend/tests/seed_test_accounts.py."
        )
    app = create_app(Config)
    with app.app_context():
        for email, password, role, full_name in DEMO_ACCOUNTS:
            user = User.query.filter_by(email=email).first()
            if user:
                user.password_hash = generate_password_hash(password)
                user.must_set_password = False
                user.credentials_delivery_pending = False
                user.is_active = True
                user.full_name = full_name
                user.role = role
            else:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    role=role,
                    full_name=full_name,
                    is_active=True,
                    must_set_password=False,
                    credentials_delivery_pending=False,
                )
                db.session.add(user)
                db.session.flush()
            if role == "faculty" and not user.faculty_profile:
                db.session.add(
                    FacultyProfile(
                        user_id=user.user_id,
                        employee_number="FAC-DEMO-001",
                        college="For Testing",
                        department="For Testing",
                        current_rank=None,
                    )
                )
        db.session.commit()
        print("Demo dev accounts ensured (faculty + reviewer).")
    return 0


if __name__ == "__main__":
    raise SystemExit(ensure())
