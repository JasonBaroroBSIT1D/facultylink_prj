"""One active reviewer per faculty — atomic assign/reassign helpers."""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from extensions import db
from models.reviewer_assignment import ReviewerAssignment


class FacultyAssignmentConflictError(Exception):
    def __init__(self, message: str, *, faculty_id: int, reviewer_id: int | None = None):
        super().__init__(message)
        self.faculty_id = faculty_id
        self.reviewer_id = reviewer_id


def active_assignment_for_faculty(faculty_id: int) -> ReviewerAssignment | None:
    return (
        ReviewerAssignment.query.filter_by(faculty_id=faculty_id, is_active=True)
        .order_by(ReviewerAssignment.assignment_id.asc())
        .first()
    )


def active_assignment_map() -> dict[int, ReviewerAssignment]:
    rows = ReviewerAssignment.query.filter_by(is_active=True).all()
    return {row.faculty_id: row for row in rows}


def set_active_reviewer_for_faculty(
    *,
    faculty_id: int,
    new_reviewer_id: int,
    assigned_by: int,
) -> ReviewerAssignment:
    """Deactivate other active rows for faculty; activate/create row for new reviewer."""
    locked = (
        ReviewerAssignment.query.filter_by(faculty_id=faculty_id)
        .order_by(ReviewerAssignment.assignment_id.asc())
        .with_for_update()
        .all()
    )
    target: ReviewerAssignment | None = None
    for row in locked:
        if row.reviewer_id == new_reviewer_id:
            target = row
        elif row.is_active:
            row.is_active = False

    if target:
        target.is_active = True
        target.assigned_by = assigned_by
        db.session.flush()
        return target

    target = ReviewerAssignment(
        reviewer_id=new_reviewer_id,
        faculty_id=faculty_id,
        assigned_by=assigned_by,
        is_active=True,
    )
    db.session.add(target)
    try:
        db.session.flush()
    except IntegrityError as exc:
        raise FacultyAssignmentConflictError(
            "Concurrent assignment update; try again.",
            faculty_id=faculty_id,
            reviewer_id=new_reviewer_id,
        ) from exc
    return target
