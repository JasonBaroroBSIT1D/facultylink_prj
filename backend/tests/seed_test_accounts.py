"""Seed demo admin/faculty/reviewer accounts on the test database only."""
from __future__ import annotations

from werkzeug.security import generate_password_hash

from extensions import db
from models import User
from models.faculty_profile import FacultyProfile

TEST_DEMO_ACCOUNTS = (
    ("admin@facultylink.edu", "demo-admin", "admin", "System Administrator"),
    ("reviewer@facultylink.edu", "demo-reviewer", "reviewer", "Faculty Reviewer"),
    ("faculty@facultylink.edu", "demo-faculty", "faculty", "Demo Faculty"),
)


def seed_test_demo_accounts() -> None:
    for email, password, role, full_name in TEST_DEMO_ACCOUNTS:
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
