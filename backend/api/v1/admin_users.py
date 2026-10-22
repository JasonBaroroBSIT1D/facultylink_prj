from __future__ import annotations

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from auth.csrf import validate_csrf
from auth.decorators import roles_required
from auth.services import create_user_account
from extensions import db
from models import User

from .reviewer_queue import queue_counts_for_reviewers

bp = Blueprint("admin_users_v1", __name__)


def _faculty_document_count(faculty_id: int) -> int:
    return int(
        db.session.execute(
            text("SELECT COUNT(*) FROM documents WHERE faculty_id = :fid"),
            {"fid": faculty_id},
        ).scalar()
        or 0
    )


def _reviewer_assignment_count(reviewer_id: int) -> int:
    return int(
        db.session.execute(
            text(
                """
                SELECT COUNT(*) FROM reviewer_assignments
                WHERE reviewer_id = :rid AND is_active = TRUE
                """
            ),
            {"rid": reviewer_id},
        ).scalar()
        or 0
    )


def _serialize_user(user: User) -> dict:
    data = user.to_public_dict(include_profile=user.role == "faculty")
    data["status_label"] = "Active" if user.is_active else "Inactive"
    if user.role == "faculty" and user.faculty_profile:
        data["document_count"] = _faculty_document_count(user.faculty_profile.faculty_id)
        data["kra_progress"] = None
    if user.role == "reviewer":
        data["assigned_faculty_count"] = _reviewer_assignment_count(user.user_id)
    return data


@bp.get("/admin/users")
@roles_required("admin")
def list_users():
    role = (request.args.get("role") or "").strip().lower()
    query = User.query.options(joinedload(User.faculty_profile))
    if role in ("faculty", "reviewer", "admin"):
        query = query.filter(User.role == role)
    elif role and role != "all":
        return jsonify({"error": "validation_error", "message": "Invalid role filter."}), 400

    users = query.order_by(User.full_name, User.email).all()
    reviewer_ids = [u.user_id for u in users if u.role == "reviewer"]
    queue_map = queue_counts_for_reviewers(reviewer_ids)
    payload = []
    for user in users:
        data = _serialize_user(user)
        if user.role == "reviewer":
            data["queue_count"] = queue_map.get(user.user_id, 0)
        payload.append(data)
    return jsonify({"users": payload})


@bp.post("/admin/users")
@roles_required("admin")
@validate_csrf
def create_user():
    body = request.get_json(silent=True) or {}
    role = (body.get("role") or "").strip().lower()
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    full_name = (body.get("full_name") or "").strip()

    if role not in ("faculty", "reviewer"):
        return jsonify({"error": "validation_error", "message": "Role must be faculty or reviewer."}), 400
    if not email or not full_name:
        return jsonify({"error": "validation_error", "message": "Email and full name are required."}), 400
    if not password:
        return jsonify({"error": "validation_error", "message": "Initial password is required."}), 400

    user, reason = create_user_account(
        email=email,
        password=password,
        role=role,
        full_name=full_name,
        employee_number=body.get("employee_number"),
        college=body.get("college"),
        department=body.get("department"),
        current_rank=body.get("current_rank"),
    )
    if not user:
        messages = {
            "duplicate_email": "An account with this email already exists.",
            "duplicate_employee_number": "Employee number is already in use.",
            "employee_number_required": "Employee number is required for faculty accounts.",
            "password_too_short": "Password must be at least 8 characters.",
        }
        status = 409 if reason in ("duplicate_email", "duplicate_employee_number") else 400
        return jsonify({"error": reason, "message": messages.get(reason, "Unable to create account.")}), status

    created = User.query.options(joinedload(User.faculty_profile)).filter_by(user_id=user.user_id).first()
    return jsonify({"user": _serialize_user(created)}), 201


@bp.patch("/admin/users/<int:user_id>")
@roles_required("admin")
@validate_csrf
def update_user(user_id: int):
    user = User.query.options(joinedload(User.faculty_profile)).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404

    body = request.get_json(silent=True) or {}

    if "is_active" in body and body["is_active"] is False and user.user_id == g.current_user.user_id:
        return jsonify(
            {
                "error": "forbidden",
                "message": "You cannot deactivate your own administrator account while signed in.",
            }
        ), 403

    if "full_name" in body and body["full_name"]:
        user.full_name = str(body["full_name"]).strip()

    if "is_active" in body:
        user.is_active = bool(body["is_active"])

    if "password" in body and body["password"]:
        if len(str(body["password"])) < 8:
            return jsonify({"error": "validation_error", "message": "Password must be at least 8 characters."}), 400
        user.password_hash = generate_password_hash(str(body["password"]))

    if user.role == "faculty":
        profile = user.faculty_profile
        if not profile and body.get("employee_number"):
            return jsonify({"error": "validation_error", "message": "Faculty profile record is missing."}), 400
        if profile:
            if "employee_number" in body and body["employee_number"]:
                existing = db.session.execute(
                    text(
                        """
                        SELECT 1 FROM faculty_profiles
                        WHERE employee_number = :num AND faculty_id <> :fid
                        """
                    ),
                    {"num": str(body["employee_number"]).strip(), "fid": profile.faculty_id},
                ).first()
                if existing:
                    return jsonify({"error": "duplicate_employee_number", "message": "Employee number is already in use."}), 409
                profile.employee_number = str(body["employee_number"]).strip()
            for field in ("college", "department", "current_rank"):
                if field in body:
                    setattr(profile, field, body[field] or None)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "database_error", "message": "Unable to save account changes."}), 500

    return jsonify({"user": _serialize_user(user)})
