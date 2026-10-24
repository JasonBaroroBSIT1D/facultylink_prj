from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from auth.csrf import validate_csrf
from auth.decorators import roles_required
from extensions import db
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule
from services.kra_i_criterion_a_metadata import (
    admin_kra_i_criterion_a_editing_payload,
    update_kra_i_criterion_a_metadata,
    validate_metadata_patch,
)

bp = Blueprint("kra_configuration_v1", __name__)


def _rule_summary(rule: ScoringRule) -> dict:
    config = rule.rule_config if isinstance(rule.rule_config, dict) else {}
    summary = {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "is_active": rule.is_active,
        "guideline_version": rule.guideline_version,
        "locked": False,
    }
    for key in ("max_points", "cap", "contribution", "multiplier", "formula", "criterion_max_points"):
        if key in config:
            summary[key] = config[key]
    return summary


def _serialize_configuration(*, include_admin_editing: bool) -> dict:
    kras = (
        KraConfiguration.query.filter_by(is_active=True)
        .order_by(KraConfiguration.kra_code)
        .all()
    )
    guideline_versions = sorted({k.guideline_version for k in kras if k.guideline_version})

    payload = []
    for kra in kras:
        criteria_payload = []
        for criterion in (
            KraCriterion.query.filter_by(kra_id=kra.kra_id).order_by(KraCriterion.display_order).all()
        ):
            indicators_payload = []
            for indicator in (
                KraIndicator.query.filter_by(criterion_id=criterion.criterion_id)
                .order_by(KraIndicator.display_order)
                .all()
            ):
                rules = (
                    ScoringRule.query.filter_by(indicator_id=indicator.indicator_id, is_active=True).all()
                )
                indicators_payload.append(
                    {
                        "indicator_id": indicator.indicator_id,
                        "code": indicator.indicator_code,
                        "name": indicator.indicator_name,
                        "required_evidence": indicator.required_evidence,
                        "scoring_rules": [_rule_summary(r) for r in rules],
                    }
                )
            criteria_payload.append(
                {
                    "criterion_id": criterion.criterion_id,
                    "code": criterion.criterion_code,
                    "name": criterion.criterion_name,
                    "description": criterion.description,
                    "indicator_count": len(indicators_payload),
                    "indicators": indicators_payload,
                }
            )
        payload.append(
            {
                "id": str(kra.kra_id),
                "kra_id": kra.kra_id,
                "code": kra.kra_code,
                "name": kra.kra_name,
                "title": f"{kra.kra_code} — {kra.kra_name}",
                "description": kra.description,
                "guideline_version": kra.guideline_version,
                "criteria_count": len(criteria_payload),
                "criteria": criteria_payload,
            }
        )

    body: dict = {
        "guideline_version": guideline_versions[0] if len(guideline_versions) == 1 else None,
        "guideline_versions": guideline_versions,
        "kras": payload,
    }
    if include_admin_editing:
        body["kra_i_criterion_a_editing"] = admin_kra_i_criterion_a_editing_payload()
    return body


@bp.get("/admin/kra-configuration")
@roles_required("admin")
def admin_kra_configuration():
    return jsonify(_serialize_configuration(include_admin_editing=True))


@bp.patch("/admin/kra-configuration/kra-i/criterion-a")
@roles_required("admin")
@validate_csrf
def patch_kra_i_criterion_a_metadata():
    validated, err = validate_metadata_patch(request.get_json(silent=True) or {})
    if err:
        return jsonify({"error": "validation_error", "message": err}), 400

    try:
        editing = update_kra_i_criterion_a_metadata(updates=validated, admin_user_id=g.current_user.user_id)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        code = str(exc)
        if code == "not_found":
            return jsonify({"error": "not_found", "message": "KRA I Criterion A is not configured yet."}), 404
        if code in ("indicator_scope", "scope", "rule_scope"):
            return jsonify(
                {"error": "validation_error", "message": "Updates are limited to KRA I Criterion A (SET/SEF)."}
            ), 400
        if code == "points_consistency":
            return jsonify(
                {
                    "error": "validation_error",
                    "message": "SET and SEF maximum points cannot exceed the Criterion A maximum.",
                }
            ), 400
        raise

    return jsonify({"kra_i_criterion_a_editing": editing})


@bp.get("/kra-configuration")
@roles_required("admin", "reviewer", "faculty")
def read_kra_configuration():
    return jsonify(_serialize_configuration(include_admin_editing=False))
