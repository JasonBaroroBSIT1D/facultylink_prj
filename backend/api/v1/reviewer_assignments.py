from __future__ import annotations

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from auth.access_control import reviewer_may_access_faculty
from auth.decorators import roles_required
from extensions import db
from models import FacultyProfile, User
from models.reviewer_assignment import ReviewerAssignment

bp = Blueprint("reviewer_assignments_v1", __name__)


def _document_count(faculty_id: int) -> int:
    return int(
        db.session.execute(
            text("SELECT COUNT(*) FROM documents WHERE faculty_id = :fid"),
            {"fid": faculty_id},
        ).scalar()
        or 0
    )


def _serialize_faculty_row(profile: FacultyProfile, user: User) -> dict:
    return {
        "id": str(profile.faculty_id),
        "faculty_id": profile.faculty_id,
        "user_id": user.user_id,
        "name": user.full_name,
        "email": user.email,
        "department": profile.department or "—",
        "rank": profile.current_rank or "—",
        "status": "Active" if user.is_active else "Inactive",
        "documents": _document_count(profile.faculty_id),
        "employee_number": profile.employee_number,
        "college": profile.college,
    }


@bp.get("/reviewer/assigned-faculty")
@roles_required("reviewer")
def list_assigned_faculty():
    q = (request.args.get("q") or "").strip().lower()
    rows = (
        ReviewerAssignment.query.options(
            joinedload(ReviewerAssignment.faculty_profile).joinedload(FacultyProfile.user)
        )
        .filter(
            ReviewerAssignment.reviewer_id == g.current_user.user_id,
            ReviewerAssignment.is_active.is_(True),
        )
        .order_by(ReviewerAssignment.assigned_at.desc())
        .all()
    )

    faculty = []
    for row in rows:
        profile = row.faculty_profile
        user = profile.user if profile else None
        if not profile or not user:
            continue
        item = _serialize_faculty_row(profile, user)
        if q:
            blob = " ".join(
                [item["name"], item["email"], item["department"], item["employee_number"] or ""]
            ).lower()
            if q not in blob:
                continue
        faculty.append(item)
    return jsonify({"faculty": faculty})


@bp.get("/reviewer/assigned-faculty/<int:faculty_id>")
@roles_required("reviewer")
def get_assigned_faculty(faculty_id: int):
    if not reviewer_may_access_faculty(g.current_user, faculty_id):
        return jsonify({"error": "forbidden", "message": "This faculty member is not assigned to you."}), 403

    profile = FacultyProfile.query.options(joinedload(FacultyProfile.user)).filter_by(faculty_id=faculty_id).first()
    if not profile or not profile.user:
        return jsonify({"error": "not_found", "message": "Faculty not found."}), 404

    return jsonify({"faculty": _serialize_faculty_row(profile, profile.user)})
