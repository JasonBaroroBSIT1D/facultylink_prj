"""Role-based record access helpers for upcoming domain APIs."""
from __future__ import annotations

from sqlalchemy import select, text

from extensions import db
from models import FacultyProfile, User
from models.faculty_profile import FacultyProfile as FP


def faculty_profile_for_user(user: User) -> FacultyProfile | None:
    if user.role != "faculty":
        return None
    return db.session.scalar(select(FP).where(FP.user_id == user.user_id))


def reviewer_may_access_faculty(reviewer: User, faculty_id: int) -> bool:
    if reviewer.role != "reviewer":
        return False
    row = db.session.execute(
        text(
            """
            SELECT 1 FROM reviewer_assignments
            WHERE reviewer_id = :reviewer_id AND faculty_id = :faculty_id AND is_active = TRUE
            """
        ),
        {"reviewer_id": reviewer.user_id, "faculty_id": faculty_id},
    ).first()
    return row is not None
