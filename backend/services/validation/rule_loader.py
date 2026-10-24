"""Load SET/SEF validation rules from JSON baseline + optional PostgreSQL operational overrides."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from flask import has_app_context

RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "criterion_a_set_sef_validation.json"


@lru_cache(maxsize=1)
def _baseline_set_sef_rules() -> dict:
    with RULES_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def baseline_confidence_thresholds() -> dict[str, float]:
    raw = _baseline_set_sef_rules().get("confidence_thresholds") or {}
    return {k: float(v) for k, v in raw.items()}


def _db_threshold_overrides() -> dict[str, float]:
    if not has_app_context():
        return {}
    try:
        from services.kra_i_criterion_a_operational import get_kra_i_criterion_a, stored_confidence_thresholds

        criterion = get_kra_i_criterion_a()
        if not criterion:
            return {}
        return stored_confidence_thresholds(criterion.criterion_id)
    except Exception:
        return {}


def load_set_sef_rules() -> dict:
    rules = deepcopy(_baseline_set_sef_rules())
    overrides = _db_threshold_overrides()
    if overrides:
        rules["confidence_thresholds"] = {
            **(rules.get("confidence_thresholds") or {}),
            **overrides,
        }
    return rules


def indicator_rule(indicator_code: str) -> dict | None:
    rules = load_set_sef_rules()
    return rules.get("indicators", {}).get(indicator_code)
