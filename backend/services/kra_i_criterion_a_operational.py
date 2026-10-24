"""KRA I Criterion A — locked official scoring vs editable operational validation settings."""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

from extensions import db
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule
from services.validation.rule_loader import baseline_confidence_thresholds

OFFICIAL_GUIDELINE_VERSION = "DBM-CHED-JC-01-2026"
CRITERION_A_MAX_POINTS = 60
SET_MAX_POINTS = 36
SEF_MAX_POINTS = 24
SET_FORMULA_LABEL = "(Overall SET Rating / 100) × 36"
SEF_FORMULA_LABEL = "(Overall SEF Rating / 100) × 24"

THRESHOLD_KEYS = ("classification_min", "field_min", "identity_min", "ocr_mean_min")
THRESHOLD_BOUNDS: dict[str, tuple[float, float]] = {
    "classification_min": (0.30, 0.95),
    "field_min": (0.30, 0.95),
    "identity_min": (0.50, 0.95),
    "ocr_mean_min": (0.20, 0.80),
}


def get_kra_i_criterion_a() -> KraCriterion | None:
    return db.session.scalar(
        select(KraCriterion)
        .join(KraConfiguration, KraConfiguration.kra_id == KraCriterion.kra_id)
        .where(
            KraConfiguration.kra_code == "KRA I",
            KraConfiguration.is_active.is_(True),
            KraCriterion.criterion_code == "A",
        )
    )


def locked_official_payload() -> dict[str, Any]:
    return {
        "guideline_version": OFFICIAL_GUIDELINE_VERSION,
        "criterion_max_points": CRITERION_A_MAX_POINTS,
        "set_max_points": SET_MAX_POINTS,
        "sef_max_points": SEF_MAX_POINTS,
        "set_formula": SET_FORMULA_LABEL,
        "sef_formula": SEF_FORMULA_LABEL,
    }


def _indicator_rule_max(indicator_code: str) -> int | None:
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return None
    indicator = db.session.scalar(
        select(KraIndicator).where(
            KraIndicator.criterion_id == criterion.criterion_id,
            KraIndicator.indicator_code == indicator_code,
        )
    )
    if not indicator:
        return None
    rule = db.session.scalar(
        select(ScoringRule).where(
            ScoringRule.indicator_id == indicator.indicator_id,
            ScoringRule.is_active.is_(True),
        )
    )
    if not rule or not isinstance(rule.rule_config, dict):
        return None
    return rule.rule_config.get("max_points")


def verify_locked_scoring_in_database() -> list[str]:
    """Return human-readable mismatches if DB scoring rules drift from official JC 01/2026."""
    issues: list[str] = []
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return issues
    kra = db.session.get(KraConfiguration, criterion.kra_id)
    if kra and kra.guideline_version and kra.guideline_version != OFFICIAL_GUIDELINE_VERSION:
        issues.append(f"KRA I guideline_version is {kra.guideline_version!r}, expected {OFFICIAL_GUIDELINE_VERSION}.")
    set_max = _indicator_rule_max("A.1")
    sef_max = _indicator_rule_max("A.2")
    if set_max is not None and int(set_max) != SET_MAX_POINTS:
        issues.append(f"SET max_points is {set_max}, expected {SET_MAX_POINTS}.")
    if sef_max is not None and int(sef_max) != SEF_MAX_POINTS:
        issues.append(f"SEF max_points is {sef_max}, expected {SEF_MAX_POINTS}.")
    return issues


def _settings_row(criterion_id: int):
    from models.kra_configuration import KraCriterionOperationalSettings

    try:
        return db.session.get(KraCriterionOperationalSettings, criterion_id)
    except ProgrammingError:
        db.session.rollback()
        return None


def stored_confidence_thresholds(criterion_id: int) -> dict[str, float]:
    row = _settings_row(criterion_id)
    if not row or not isinstance(row.confidence_thresholds, dict):
        return {}
    out: dict[str, float] = {}
    for key in THRESHOLD_KEYS:
        if key in row.confidence_thresholds:
            out[key] = float(row.confidence_thresholds[key])
    return out


def effective_confidence_thresholds(criterion_id: int | None = None) -> dict[str, float]:
    base = baseline_confidence_thresholds()
    cid = criterion_id
    if cid is None:
        criterion = get_kra_i_criterion_a()
        cid = criterion.criterion_id if criterion else None
    if cid is None:
        return base
    merged = dict(base)
    merged.update(stored_confidence_thresholds(cid))
    return merged


def admin_operational_editing_payload() -> dict[str, Any] | None:
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return None
    defaults = baseline_confidence_thresholds()
    effective = effective_confidence_thresholds(criterion.criterion_id)
    row = _settings_row(criterion.criterion_id)
    return {
        "criterion_id": criterion.criterion_id,
        "criterion_code": criterion.criterion_code,
        "criterion_name": criterion.criterion_name,
        "locked_official": locked_official_payload(),
        "locked_scoring_issues": verify_locked_scoring_in_database(),
        "confidence_thresholds": effective,
        "confidence_threshold_defaults": defaults,
        "confidence_threshold_bounds": {
            key: {"min": THRESHOLD_BOUNDS[key][0], "max": THRESHOLD_BOUNDS[key][1]} for key in THRESHOLD_KEYS
        },
        "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
    }


def validate_confidence_thresholds_patch(payload: dict) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "Provide confidence_thresholds as an object."
    unknown = [k for k in payload if k not in THRESHOLD_KEYS]
    if unknown:
        return None, f"Unsupported threshold keys: {', '.join(unknown)}."
    if not payload:
        return None, "Provide at least one confidence threshold to update."
    out: dict[str, float] = {}
    for key, raw in payload.items():
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None, f"{key} must be a number."
        lo, hi = THRESHOLD_BOUNDS[key]
        if value < lo or value > hi:
            return None, f"{key} must be between {lo} and {hi}."
        out[key] = round(value, 4)
    return out, None


def save_confidence_thresholds(*, criterion_id: int, updates: dict[str, float], admin_user_id: int) -> dict[str, float]:
    from models.kra_configuration import KraCriterionOperationalSettings

    criterion = db.session.get(KraCriterion, criterion_id)
    if not criterion:
        raise ValueError("not_found")
    kra = db.session.get(KraConfiguration, criterion.kra_id)
    if not kra or kra.kra_code != "KRA I" or criterion.criterion_code != "A":
        raise ValueError("scope")

    row = db.session.get(KraCriterionOperationalSettings, criterion_id)
    before = deepcopy(row.confidence_thresholds) if row and isinstance(row.confidence_thresholds, dict) else {}
    merged = dict(before)
    merged.update(updates)
    if row:
        row.confidence_thresholds = merged
        row.updated_by = admin_user_id
    else:
        row = KraCriterionOperationalSettings(
            criterion_id=criterion_id,
            confidence_thresholds=merged,
            updated_by=admin_user_id,
        )
        db.session.add(row)
    db.session.flush()
    _append_audit(
        admin_user_id=admin_user_id,
        criterion_id=criterion_id,
        before=before,
        after=merged,
    )
    return effective_confidence_thresholds(criterion_id)


def _append_audit(*, admin_user_id: int, criterion_id: int, before: dict, after: dict) -> None:
    db.session.execute(
        text(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (:user_id, :action, :entity_type, :entity_id, CAST(:details AS jsonb))
            """
        ),
        {
            "user_id": admin_user_id,
            "action": "kra_i_criterion_a_operational_update",
            "entity_type": "kra_criterion_operational_settings",
            "entity_id": str(criterion_id),
            "details": json.dumps(
                {
                    "criterion_code": "A",
                    "kra_code": "KRA I",
                    "before": before,
                    "after": after,
                }
            ),
        },
    )
