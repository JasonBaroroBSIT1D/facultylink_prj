from __future__ import annotations

from flask import Blueprint, g, jsonify, request
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from auth.csrf import validate_csrf
from auth.decorators import roles_required
from extensions import db
from models import FacultyProfile, User
from models.reviewer_assignment import ReviewerAssignment

bp = Blueprint("admin_reviewer_assignments_v1", __name__)


def _document_count(faculty_id: int) -> int:
    return int(
        db.session.execute(
            text("SELECT COUNT(*) FROM documents WHERE faculty_id = :fid"),
            {"fid": faculty_id},
        ).scalar()
        or 0
    )


def _serialize_assignment(row: ReviewerAssignment) -> dict:
    profile = row.faculty_profile
    user = profile.user if profile else None
    return {
        "assignment_id": row.assignment_id,
        "reviewer_id": row.reviewer_id,
        "faculty_id": row.faculty_id,
        "is_active": row.is_active,
        "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
        "faculty": {
            "faculty_id": profile.faculty_id if profile else row.faculty_id,
            "user_id": profile.user_id if profile else None,
            "full_name": user.full_name if user else "",
            "email": user.email if user else "",
            "employee_number": profile.employee_number if profile else "",
            "department": profile.department if profile else "",
            "college": profile.college if profile else "",
            "current_rank": profile.current_rank if profile else "",
            "is_active": user.is_active if user else False,
            "document_count": _document_count(row.faculty_id),
        },
    }


def _load_reviewer(reviewer_id: int) -> User | None:
    user = db.session.get(User, reviewer_id)
    if not user or user.role != "reviewer":
        return None
    return user


@bp.get("/admin/reviewers/<int:reviewer_id>/assignments")
@roles_required("admin")
def list_reviewer_assignments(reviewer_id: int):
    reviewer = _load_reviewer(reviewer_id)
    if not reviewer:
        return jsonify({"error": "not_found", "message": "Reviewer not found."}), 404

    active_only = request.args.get("active", "true").lower() != "false"
    query = (
        ReviewerAssignment.query.options(
            joinedload(ReviewerAssignment.faculty_profile).joinedload(FacultyProfile.user)
        )
        .filter(ReviewerAssignment.reviewer_id == reviewer_id)
        .order_by(ReviewerAssignment.assigned_at.desc())
    )
    if active_only:
        query = query.filter(ReviewerAssignment.is_active.is_(True))
    rows = query.all()
    return jsonify({"assignments": [_serialize_assignment(r) for r in rows]})


@bp.get("/admin/reviewers/<int:reviewer_id>/assignment-candidates")
@roles_required("admin")
def assignment_candidates(reviewer_id: int):
    reviewer = _load_reviewer(reviewer_id)
    if not reviewer:
        return jsonify({"error": "not_found", "message": "Reviewer not found."}), 404

    q = (request.args.get("q") or "").strip().lower()
    assigned_ids = {
        row.faculty_id
        for row in db.session.scalars(
            select(ReviewerAssignment.faculty_id).where(
                ReviewerAssignment.reviewer_id == reviewer_id,
                ReviewerAssignment.is_active.is_(True),
            )
        )
    }

    profiles = (
        FacultyProfile.query.options(joinedload(FacultyProfile.user))
        .join(User, FacultyProfile.user_id == User.user_id)
        .filter(User.role == "faculty", User.is_active.is_(True))
        .order_by(User.full_name)
        .all()
    )

    candidates = []
    for profile in profiles:
        user = profile.user
        if q:
            blob = " ".join(
                [
                    user.full_name or "",
                    user.email or "",
                    profile.employee_number or "",
                    profile.department or "",
                ]
            ).lower()
            if q and q not in blob:
                continue
        candidates.append(
            {
                "faculty_id": profile.faculty_id,
                "full_name": user.full_name,
                "email": user.email,
                "department": profile.department,
                "current_rank": profile.current_rank,
                "already_assigned": profile.faculty_id in assigned_ids,
            }
        )
    return jsonify({"candidates": candidates})


@bp.post("/admin/reviewers/<int:reviewer_id>/assignments")
@roles_required("admin")
@validate_csrf
def create_assignments(reviewer_id: int):
    reviewer = _load_reviewer(reviewer_id)
    if not reviewer:
        return jsonify({"error": "not_found", "message": "Reviewer not found."}), 404
    if not reviewer.is_active:
        return jsonify({"error": "validation_error", "message": "Cannot assign faculty to an inactive reviewer."}), 400

    body = request.get_json(silent=True) or {}
    faculty_ids = body.get("faculty_ids")
    if not isinstance(faculty_ids, list) or not faculty_ids:
        return jsonify({"error": "validation_error", "message": "Provide one or more faculty_ids."}), 400

    created = []
    reactivated = []
    skipped = []
    errors = []

    try:
        for raw_id in faculty_ids:
            try:
                faculty_id = int(raw_id)
            except (TypeError, ValueError):
                errors.append({"faculty_id": raw_id, "reason": "invalid_id"})
                continue

            profile = db.session.get(FacultyProfile, faculty_id)
            if not profile:
                errors.append({"faculty_id": faculty_id, "reason": "not_found"})
                continue
            faculty_user = db.session.get(User, profile.user_id)
            if not faculty_user or faculty_user.role != "faculty" or not faculty_user.is_active:
                errors.append({"faculty_id": faculty_id, "reason": "inactive_or_invalid_faculty"})
                continue

            existing = ReviewerAssignment.query.filter_by(
                reviewer_id=reviewer_id, faculty_id=faculty_id
            ).first()
            if existing:
                if existing.is_active:
                    skipped.append(faculty_id)
                    continue
                existing.is_active = True
                existing.assigned_by = g.current_user.user_id
                reactivated.append(faculty_id)
                continue

            row = ReviewerAssignment(
                reviewer_id=reviewer_id,
                faculty_id=faculty_id,
                assigned_by=g.current_user.user_id,
                is_active=True,
            )
            db.session.add(row)
            created.append(faculty_id)

        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "server_error", "message": "Unable to save assignments."}), 500

    rows = (
        ReviewerAssignment.query.options(
            joinedload(ReviewerAssignment.faculty_profile).joinedload(FacultyProfile.user)
        )
        .filter(
            ReviewerAssignment.reviewer_id == reviewer_id,
            ReviewerAssignment.is_active.is_(True),
        )
        .order_by(ReviewerAssignment.assigned_at.desc())
        .all()
    )
    return jsonify(
        {
            "created": created,
            "reactivated": reactivated,
            "skipped": skipped,
            "errors": errors,
            "assignments": [_serialize_assignment(r) for r in rows],
        }
    ), 201


@bp.patch("/admin/reviewer-assignments/<int:assignment_id>")
@roles_required("admin")
@validate_csrf
def update_assignment(assignment_id: int):
    row = ReviewerAssignment.query.options(
        joinedload(ReviewerAssignment.faculty_profile).joinedload(FacultyProfile.user)
    ).filter_by(assignment_id=assignment_id).first()
    if not row:
        return jsonify({"error": "not_found", "message": "Assignment not found."}), 404

    body = request.get_json(silent=True) or {}

    if "is_active" in body:
        row.is_active = bool(body["is_active"])

    if "reviewer_id" in body:
        new_reviewer_id = int(body["reviewer_id"])
        new_reviewer = _load_reviewer(new_reviewer_id)
        if not new_reviewer or not new_reviewer.is_active:
            return jsonify({"error": "validation_error", "message": "Target reviewer is invalid or inactive."}), 400
        if new_reviewer_id == row.reviewer_id:
            pass
        else:
            try:
                with db.session.begin_nested():
                    conflict = (
                        ReviewerAssignment.query.filter_by(
                            reviewer_id=new_reviewer_id, faculty_id=row.faculty_id
                        )
                        .with_for_update()
                        .first()
                    )
                    if conflict and conflict.is_active and conflict.assignment_id != row.assignment_id:
                        raise ValueError("duplicate_assignment")
                    if conflict and not conflict.is_active:
                        conflict.is_active = True
                        conflict.assigned_by = g.current_user.user_id
                        row.is_active = False
                    else:
                        row.reviewer_id = new_reviewer_id
                        row.assigned_by = g.current_user.user_id
                        row.is_active = True
            except ValueError as exc:
                if str(exc) == "duplicate_assignment":
                    return jsonify(
                        {
                            "error": "duplicate_assignment",
                            "message": "This faculty member is already assigned to the selected reviewer.",
                        }
                    ), 409
                raise

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "server_error", "message": "Unable to update assignment."}), 500

    return jsonify({"assignment": _serialize_assignment(row)})
