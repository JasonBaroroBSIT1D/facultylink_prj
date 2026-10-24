"""Admin Validation & Scoring settings (KRA I Criterion A SET/SEF operational thresholds)."""
from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from auth.csrf import validate_csrf
from auth.decorators import roles_required
from extensions import db
from services.kra_i_criterion_a_operational import (
    admin_operational_editing_payload,
    get_kra_i_criterion_a,
    save_confidence_thresholds,
    validate_confidence_thresholds_patch,
)

bp = Blueprint("validation_scoring_config_v1", __name__)


@bp.get("/admin/validation-scoring/kra-i/criterion-a")
@roles_required("admin")
def get_criterion_a_validation_scoring():
    operational = admin_operational_editing_payload()
    if not operational:
        return jsonify(
            {"error": "not_found", "message": "KRA I Criterion A is not configured in PostgreSQL yet."}
        ), 404
    return jsonify({"operational": operational})


@bp.patch("/admin/validation-scoring/kra-i/criterion-a/operational-settings")
@roles_required("admin")
@validate_csrf
def patch_criterion_a_operational_settings():
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return jsonify(
            {"error": "not_found", "message": "KRA I Criterion A is not configured in PostgreSQL yet."}
        ), 404

    body = request.get_json(silent=True) or {}
    forbidden = [k for k in body if k != "confidence_thresholds"]
    if forbidden:
        return jsonify(
            {
                "error": "validation_error",
                "message": "Only confidence_thresholds may be edited on this endpoint.",
            }
        ), 400

    validated, err = validate_confidence_thresholds_patch(body.get("confidence_thresholds") or {})
    if err:
        return jsonify({"error": "validation_error", "message": err}), 400

    try:
        effective = save_confidence_thresholds(
            criterion_id=criterion.criterion_id,
            updates=validated,
            admin_user_id=g.current_user.user_id,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        if str(exc) == "not_found":
            return jsonify({"error": "not_found", "message": "Criterion not found."}), 404
        if str(exc) == "scope":
            return jsonify({"error": "validation_error", "message": "Edits are limited to KRA I Criterion A."}), 400
        raise

    operational = admin_operational_editing_payload()
    if operational:
        operational["confidence_thresholds"] = effective
    return jsonify({"operational": operational})
