from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from auth.csrf import validate_csrf
from auth.decorators import roles_required
from extensions import db
from models.evaluation_period import EvaluationPeriod

from .period_utils import parse_period_instant, period_status, serialize_evaluation_period

bp = Blueprint("evaluation_periods_v1", __name__)


def _find_overlaps(opens_at: datetime, closes_at: datetime, exclude_id: int | None = None):
    query = EvaluationPeriod.query.filter(
        EvaluationPeriod.opens_at < closes_at,
        EvaluationPeriod.closes_at > opens_at,
    )
    if exclude_id is not None:
        query = query.filter(EvaluationPeriod.period_id != exclude_id)
    return query.all()


def _validate_period_body(body: dict, *, partial: bool = False) -> tuple[dict | None, str | None]:
    errors: dict[str, str] = {}
    data: dict = {}

    def need(field: str, key: str | None = None):
        key = key or field
        if key in body or not partial:
            val = body.get(key)
            if val is None or (isinstance(val, str) and not str(val).strip()):
                errors[key] = "This field is required."

    need("name")
    need("academic_year", "academicYear")
    need("semester")
    need("opens_at", "opensAt")
    need("closes_at", "closesAt")

    if errors:
        return None, errors

    opens_raw = body.get("opensAt") if "opensAt" in body or not partial else None
    closes_raw = body.get("closesAt") if "closesAt" in body or not partial else None

    opens_at = parse_period_instant(opens_raw) if opens_raw is not None else None
    closes_at = parse_period_instant(closes_raw) if closes_raw is not None else None

    if opens_raw is not None and not opens_at:
        errors["opensAt"] = "Enter a valid opening date and time (Asia/Manila)."
    if closes_raw is not None and not closes_at:
        errors["closesAt"] = "Enter a valid closing date and time (Asia/Manila)."
    if opens_at and closes_at and closes_at <= opens_at:
        errors["closesAt"] = "Closing must be later than opening."

    if errors:
        return None, errors

    if "name" in body or not partial:
        data["name"] = str(body.get("name", "")).strip()
    if "academicYear" in body or not partial:
        data["academic_year"] = str(body.get("academicYear", "")).strip()
    if "semester" in body or not partial:
        data["semester"] = str(body.get("semester", "")).strip()
    if opens_at:
        data["opens_at"] = opens_at
    if closes_at:
        data["closes_at"] = closes_at
    if "description" in body:
        data["description"] = str(body.get("description") or "").strip()
    if "submissionEnabled" in body:
        data["submission_enabled"] = bool(body.get("submissionEnabled"))
    if "reviewEnabled" in body:
        data["review_enabled"] = bool(body.get("reviewEnabled"))
    if "period_code" in body:
        code = str(body.get("period_code") or "").strip() or None
        data["period_code"] = code

    return data, None


@bp.get("/evaluation-periods")
@roles_required("admin", "reviewer", "faculty")
def list_evaluation_periods():
    rows = EvaluationPeriod.query.order_by(EvaluationPeriod.opens_at.asc()).all()
    return jsonify({"periods": [serialize_evaluation_period(p) for p in rows]})


@bp.post("/admin/evaluation-periods")
@roles_required("admin")
@validate_csrf
def create_evaluation_period():
    body = request.get_json(silent=True) or {}
    data, errors = _validate_period_body(body, partial=False)
    if errors:
        return jsonify({"error": "validation_error", "message": "Check the evaluation period details.", "fields": errors}), 400

    acknowledge = bool(body.get("acknowledge_overlap") or body.get("acknowledgeOverlap"))
    overlaps = _find_overlaps(data["opens_at"], data["closes_at"])
    if overlaps and not acknowledge:
        return jsonify(
            {
                "error": "overlap",
                "message": "This window overlaps another evaluation period.",
                "overlaps": [serialize_evaluation_period(p) for p in overlaps],
            }
        ), 409

    period = EvaluationPeriod(
        name=data["name"],
        academic_year=data["academic_year"],
        semester=data["semester"],
        opens_at=data["opens_at"],
        closes_at=data["closes_at"],
        description=data.get("description", ""),
        submission_enabled=data.get("submission_enabled", True),
        review_enabled=data.get("review_enabled", True),
        period_code=data.get("period_code"),
        timezone="Asia/Manila",
    )
    try:
        db.session.add(period)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "duplicate", "message": "A period with this code already exists."}), 409

    return jsonify({"period": serialize_evaluation_period(period)}), 201


@bp.patch("/admin/evaluation-periods/<int:period_id>")
@roles_required("admin")
@validate_csrf
def update_evaluation_period(period_id: int):
    period = db.session.get(EvaluationPeriod, period_id)
    if not period:
        return jsonify({"error": "not_found", "message": "Evaluation period not found."}), 404

    body = request.get_json(silent=True) or {}
    errors: dict[str, str] = {}

    opens_at = period.opens_at
    closes_at = period.closes_at
    if "opensAt" in body:
        opens_at = parse_period_instant(body["opensAt"])
        if not opens_at:
            errors["opensAt"] = "Enter a valid opening date and time (Asia/Manila)."
    if "closesAt" in body:
        closes_at = parse_period_instant(body["closesAt"])
        if not closes_at:
            errors["closesAt"] = "Enter a valid closing date and time (Asia/Manila)."
    if opens_at and closes_at and closes_at <= opens_at:
        errors["closesAt"] = "Closing must be later than opening."

    for field in ("name", "academicYear", "semester"):
        if field in body and not str(body[field]).strip():
            errors[field] = "This field is required."

    if errors:
        return jsonify({"error": "validation_error", "message": "Check the evaluation period details.", "fields": errors}), 400

    acknowledge = bool(body.get("acknowledge_overlap") or body.get("acknowledgeOverlap"))
    overlaps = _find_overlaps(opens_at, closes_at, exclude_id=period_id)
    if overlaps and not acknowledge:
        return jsonify(
            {
                "error": "overlap",
                "message": "This window overlaps another evaluation period.",
                "overlaps": [serialize_evaluation_period(p) for p in overlaps],
            }
        ), 409

    if "name" in body:
        period.name = str(body["name"]).strip()
    if "academicYear" in body:
        period.academic_year = str(body["academicYear"]).strip()
    if "semester" in body:
        period.semester = str(body["semester"]).strip()
    if "opensAt" in body and opens_at:
        period.opens_at = opens_at
    if "closesAt" in body and closes_at:
        period.closes_at = closes_at
    if "description" in body:
        period.description = str(body.get("description") or "").strip()
    if "submissionEnabled" in body:
        period.submission_enabled = bool(body["submissionEnabled"])
    if "reviewEnabled" in body:
        period.review_enabled = bool(body["reviewEnabled"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "duplicate", "message": "Unable to save evaluation period."}), 409

    return jsonify({"period": serialize_evaluation_period(period)})


@bp.post("/admin/evaluation-periods/<int:period_id>/close-early")
@roles_required("admin")
@validate_csrf
def close_evaluation_period_early(period_id: int):
    period = db.session.get(EvaluationPeriod, period_id)
    if not period:
        return jsonify({"error": "not_found", "message": "Evaluation period not found."}), 404

    now = datetime.now(timezone.utc)
    if period_status(period, now) != "Open":
        return jsonify({"error": "validation_error", "message": "Only an open period can be closed early."}), 400

    opens = period.opens_at if period.opens_at.tzinfo else period.opens_at.replace(tzinfo=timezone.utc)
    if now <= opens:
        return jsonify({"error": "validation_error", "message": "The period is not open yet."}), 400

    period.closes_at = now
    db.session.commit()
    return jsonify({"period": serialize_evaluation_period(period)})
