"""Test helpers — cleanup and isolation utilities."""
from __future__ import annotations

from extensions import db
from models import PasswordResetOtp, PasswordToken, User
from models.faculty_profile import FacultyProfile
from models.reviewer_assignment import ReviewerAssignment


def delete_test_user_cascade(user_id: int) -> None:
    """Remove a disposable test user and known FK rows (no CASCADE)."""
    db.session.query(ReviewerAssignment).filter_by(reviewer_id=user_id).delete()
    db.session.query(PasswordResetOtp).filter_by(user_id=user_id).delete()
    db.session.query(PasswordToken).filter_by(user_id=user_id).delete()
    db.session.query(FacultyProfile).filter_by(user_id=user_id).delete()
    db.session.query(User).filter_by(user_id=user_id).delete()
    db.session.commit()


def is_test_email(email: str) -> bool:
    return (email or "").endswith("@facultylink.test")
