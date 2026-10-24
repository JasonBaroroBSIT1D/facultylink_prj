from __future__ import annotations

from flask import Blueprint, jsonify

from auth.decorators import roles_required
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule

bp = Blueprint("kra_configuration_v1", __name__)


def _rule_summary(rule: ScoringRule) -> dict:
    config = rule.rule_config if isinstance(rule.rule_config, dict) else {}
    summary = {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "is_active": rule.is_active,
        "guideline_version": rule.guideline_version,
    }
    for key in ("max_points", "cap", "contribution", "multiplier"):
        if key in config:
            summary[key] = config[key]
    if config:
        summary["rule_config"] = config
    return summary


def _serialize_configuration() -> dict:
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

    return {
        "guideline_version": guideline_versions[0] if len(guideline_versions) == 1 else None,
        "guideline_versions": guideline_versions,
        "kras": payload,
    }


@bp.get("/admin/kra-configuration")
@roles_required("admin")
def admin_kra_configuration():
    return jsonify(_serialize_configuration())


@bp.get("/kra-configuration")
@roles_required("admin", "reviewer", "faculty")
def read_kra_configuration():
    return jsonify(_serialize_configuration())
