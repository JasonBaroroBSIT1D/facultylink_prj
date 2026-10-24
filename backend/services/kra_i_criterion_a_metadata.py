"""Editable metadata and scoring for KRA I Criterion A (SET/SEF)."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from extensions import db
from models.kra_configuration import KraCriterion, KraIndicator
from services.kra_i_criterion_a_operational import get_kra_i_criterion_a, locked_official_payload
from services.kra_i_criterion_a_scoring import (
    apply_scoring_updates,
    configuration_profile,
    serialize_scoring_rules_for_admin,
    validate_scoring_patch,
)

ALLOWED_INDICATOR_CODES = frozenset({"A.1", "A.2"})
MAX_NAME_LEN = 200
MAX_DESCRIPTION_LEN = 8000
MAX_EVIDENCE_LEN = 8000


def admin_kra_i_criterion_a_editing_payload() -> dict[str, Any] | None:
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return None
    indicators = (
        KraIndicator.query.filter_by(criterion_id=criterion.criterion_id)
        .order_by(KraIndicator.display_order)
        .all()
    )
    profile = configuration_profile()
    scoring_rules = serialize_scoring_rules_for_admin(criterion.criterion_id)
    return {
        "criterion_id": criterion.criterion_id,
        "criterion_code": criterion.criterion_code,
        "criterion_name": criterion.criterion_name,
        "description": criterion.description,
        "locked_official": locked_official_payload(),
        "configuration_profile": profile,
        "locked_scoring_issues": profile.get("issues") or [],
        "scoring_rules_locked": scoring_rules,
        "scoring_rules": scoring_rules,
        "indicators": [
            {
                "indicator_id": ind.indicator_id,
                "code": ind.indicator_code,
                "name": ind.indicator_name,
                "required_evidence": ind.required_evidence,
            }
            for ind in indicators
            if ind.indicator_code in ALLOWED_INDICATOR_CODES
        ],
    }


def _clean_text(value: object, *, field: str, max_len: int, required: bool = False) -> tuple[str | None, str | None]:
    if value is None:
        if required:
            return None, f"{field} is required."
        return None, None
    if not isinstance(value, str):
        return None, f"{field} must be a string."
    text = value.strip()
    if required and not text:
        return None, f"{field} is required."
    if len(text) > max_len:
        return None, f"{field} must be at most {max_len} characters."
    return text or None, None


def validate_metadata_patch(body: dict) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(body, dict):
        return None, "Invalid request body."

    scoring_part, scoring_err = validate_scoring_patch(body)
    if scoring_err:
        return None, scoring_err

    if body.get("restore_official_defaults"):
        return scoring_part, None

    allowed = {
        "criterion_name",
        "description",
        "indicators",
        "criterion_max_points",
        "scoring_rules",
        "restore_official_defaults",
    }
    forbidden = [k for k in body if k not in allowed]
    if forbidden:
        return None, f"Unsupported fields: {', '.join(forbidden)}."

    out: dict[str, Any] = dict(scoring_part or {})
    if "criterion_name" in body:
        name, err = _clean_text(body["criterion_name"], field="criterion_name", max_len=MAX_NAME_LEN, required=True)
        if err:
            return None, err
        out["criterion_name"] = name
    if "description" in body:
        desc, err = _clean_text(body["description"], field="description", max_len=MAX_DESCRIPTION_LEN)
        if err:
            return None, err
        out["description"] = desc

    if "indicators" in body:
        raw = body["indicators"]
        if not isinstance(raw, list) or not raw:
            return None, "Provide one or more indicators to update."
        parsed: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                return None, "Each indicator entry must be an object."
            try:
                indicator_id = int(item["indicator_id"])
            except (KeyError, TypeError, ValueError):
                return None, "Each indicator requires a valid indicator_id."
            entry: dict[str, Any] = {"indicator_id": indicator_id}
            if "indicator_name" in item:
                name, err = _clean_text(
                    item["indicator_name"], field="indicator_name", max_len=MAX_NAME_LEN, required=True
                )
                if err:
                    return None, err
                entry["indicator_name"] = name
            if "required_evidence" in item:
                ev, err = _clean_text(item["required_evidence"], field="required_evidence", max_len=MAX_EVIDENCE_LEN)
                if err:
                    return None, err
                entry["required_evidence"] = ev
            if len(entry) == 1:
                return None, "Each indicator must include indicator_name and/or required_evidence."
            parsed.append(entry)
        out["indicators"] = parsed

    if not out:
        return None, "Provide at least one field to update."
    return out, None


def update_kra_i_criterion_a_metadata(*, updates: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    criterion = get_kra_i_criterion_a()
    if not criterion:
        raise ValueError("not_found")

    if updates.get("restore_official_defaults") or updates.get("scoring_rules") or "criterion_max_points" in updates:
        try:
            apply_scoring_updates(updates=updates, admin_user_id=admin_user_id)
        except ValueError as exc:
            code = str(exc)
            if code == "points_consistency":
                raise ValueError("points_consistency") from exc
            if code == "rule_scope":
                raise ValueError("rule_scope") from exc
            raise

    before = {
        "criterion_name": criterion.criterion_name,
        "description": criterion.description,
        "indicators": {},
    }
    allowed_inds = {
        ind.indicator_id: ind
        for ind in KraIndicator.query.filter_by(criterion_id=criterion.criterion_id).all()
        if ind.indicator_code in ALLOWED_INDICATOR_CODES
    }
    for ind in allowed_inds.values():
        before["indicators"][str(ind.indicator_id)] = {
            "code": ind.indicator_code,
            "indicator_name": ind.indicator_name,
            "required_evidence": ind.required_evidence,
        }

    metadata_touched = False
    if "criterion_name" in updates:
        criterion.criterion_name = updates["criterion_name"]
        metadata_touched = True
    if "description" in updates:
        criterion.description = updates["description"]
        metadata_touched = True

    if "indicators" in updates:
        metadata_touched = True
        for item in updates["indicators"]:
            ind = allowed_inds.get(item["indicator_id"])
            if not ind:
                raise ValueError("indicator_scope")
            if "indicator_name" in item:
                ind.indicator_name = item["indicator_name"]
            if "required_evidence" in item:
                ind.required_evidence = item["required_evidence"]

    after = {
        "criterion_name": criterion.criterion_name,
        "description": criterion.description,
        "indicators": {
            str(ind_id): {
                "code": ind.indicator_code,
                "indicator_name": ind.indicator_name,
                "required_evidence": ind.required_evidence,
            }
            for ind_id, ind in allowed_inds.items()
        },
    }

    if metadata_touched:
        db.session.flush()
        _append_metadata_audit(admin_user_id=admin_user_id, criterion_id=criterion.criterion_id, before=before, after=after)

    payload = admin_kra_i_criterion_a_editing_payload()
    return payload or {}


def _append_metadata_audit(*, admin_user_id: int, criterion_id: int, before: dict, after: dict) -> None:
    db.session.execute(
        text(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (:user_id, :action, :entity_type, :entity_id, CAST(:details AS jsonb))
            """
        ),
        {
            "user_id": admin_user_id,
            "action": "kra_i_criterion_a_metadata_update",
            "entity_type": "kra_criterion",
            "entity_id": str(criterion_id),
            "details": json.dumps(
                {
                    "kra_code": "KRA I",
                    "criterion_code": "A",
                    "before": before,
                    "after": after,
                }
            ),
        },
    )


def assert_indicator_in_kra_i_criterion_a(indicator_id: int) -> KraIndicator:
    indicator = db.session.get(KraIndicator, indicator_id)
    if not indicator:
        raise ValueError("not_found")
    criterion = get_kra_i_criterion_a()
    if not criterion or indicator.criterion_id != criterion.criterion_id:
        raise ValueError("indicator_scope")
    if indicator.indicator_code not in ALLOWED_INDICATOR_CODES:
        raise ValueError("indicator_scope")
    return indicator
