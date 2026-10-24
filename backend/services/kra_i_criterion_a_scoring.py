"""KRA I Criterion A — editable scoring config, safe formulas, and point calculation."""
from __future__ import annotations

import ast
import json
import math
import operator
from typing import Any

from sqlalchemy import select, text

from extensions import db
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule
from services.kra_i_criterion_a_operational import (
    CRITERION_A_MAX_POINTS,
    OFFICIAL_GUIDELINE_VERSION,
    SEF_MAX_POINTS,
    SET_MAX_POINTS,
    get_kra_i_criterion_a,
)

ALLOWED_INDICATOR_CODES = frozenset({"A.1", "A.2"})
DEFAULT_FORMULA = "(rating / 100) * max_points"
OFFICIAL_FORMULAS = {
    "A.1": DEFAULT_FORMULA,
    "A.2": DEFAULT_FORMULA,
}
MAX_CRITERION_POINTS = 100
MAX_INDICATOR_POINTS = 100

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _official_rule_name(indicator_code: str) -> str:
    if indicator_code == "A.1":
        return "SET — (Overall SET Rating / 100) × 36"
    return "SEF — (Overall SEF Rating / 100) × 24"


def official_rule_config(*, indicator_code: str, criterion_max: int | None = None) -> dict[str, Any]:
    crit = criterion_max if criterion_max is not None else CRITERION_A_MAX_POINTS
    max_pts = SET_MAX_POINTS if indicator_code == "A.1" else SEF_MAX_POINTS
    input_field = "overall_set_rating" if indicator_code == "A.1" else "overall_sef_rating"
    return {
        "input_field": input_field,
        "input_min": 0,
        "input_max": 100,
        "max_points": max_pts,
        "formula": DEFAULT_FORMULA,
        "criterion_max_points": crit,
        "rating_divisor": 100,
    }


def validate_formula_expression(formula: str) -> tuple[str | None, str | None]:
    if not isinstance(formula, str) or not formula.strip():
        return None, "formula is required."
    expr = formula.strip()
    if len(expr) > 200:
        return None, "formula is too long."
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None, "formula syntax is invalid."
    allowed_names = {"rating", "max_points"}

    def _walk(node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            _walk(node.body)
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("only numeric constants allowed")
        elif isinstance(node, ast.Name):
            if node.id not in allowed_names:
                raise ValueError(f"unknown name {node.id}")
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _BINOPS:
                raise ValueError("unsupported operator")
            _walk(node.left)
            _walk(node.right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in _UNARYOPS:
                raise ValueError("unsupported unary operator")
            _walk(node.operand)
        else:
            raise ValueError("unsupported expression")

    try:
        _walk(tree)
    except ValueError as exc:
        return None, str(exc)
    try:
        sample = evaluate_formula(expr, rating=50.0, max_points=36.0)
        if not math.isfinite(sample):
            return None, "formula must produce a finite number for sample inputs."
    except Exception:
        return None, "formula could not be evaluated with sample inputs."
    return expr, None


def evaluate_formula(formula: str, *, rating: float, max_points: float) -> float:
    tree = ast.parse(formula.strip(), mode="eval")
    env = {"rating": float(rating), "max_points": float(max_points)}

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return float(env[node.id])
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            return float(_BINOPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp):
            return float(_UNARYOPS[type(node.op)](_eval(node.operand)))
        raise ValueError("unsupported expression")

    return _eval(tree)


def calculate_points_from_rule(*, rating: float, rule_config: dict) -> float:
    max_pts = float(rule_config.get("max_points") or 0)
    if max_pts <= 0:
        return 0.0
    formula = rule_config.get("formula") or DEFAULT_FORMULA
    raw = evaluate_formula(str(formula), rating=float(rating), max_points=max_pts)
    capped = min(max_pts, max(0.0, raw))
    return round(capped, 4)


def _active_rule(indicator_id: int) -> ScoringRule | None:
    return db.session.scalar(
        select(ScoringRule).where(ScoringRule.indicator_id == indicator_id, ScoringRule.is_active.is_(True))
    )


def load_indicator_scoring(indicator: KraIndicator) -> dict[str, Any] | None:
    rule = _active_rule(indicator.indicator_id)
    if not rule:
        return None
    cfg = rule.rule_config if isinstance(rule.rule_config, dict) else {}
    return {
        "rule_id": rule.rule_id,
        "indicator_id": indicator.indicator_id,
        "indicator_code": indicator.indicator_code,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "guideline_version": rule.guideline_version,
        "rule_config": cfg,
    }


def configuration_profile() -> dict[str, Any]:
    """Return official reference, effective DB values, and custom vs official label."""
    criterion = get_kra_i_criterion_a()
    if not criterion:
        return {"configuration_label": "unconfigured", "issues": ["KRA I Criterion A is not configured."]}
    indicators = (
        KraIndicator.query.filter_by(criterion_id=criterion.criterion_id)
        .order_by(KraIndicator.display_order)
        .all()
    )
    set_row = next((i for i in indicators if i.indicator_code == "A.1"), None)
    sef_row = next((i for i in indicators if i.indicator_code == "A.2"), None)
    set_cfg = load_indicator_scoring(set_row) if set_row else None
    sef_cfg = load_indicator_scoring(sef_row) if sef_row else None
    crit_max = None
    for cfg in (set_cfg, sef_cfg):
        if cfg and isinstance(cfg.get("rule_config"), dict):
            crit_max = cfg["rule_config"].get("criterion_max_points")
            if crit_max is not None:
                break
    set_max = (set_cfg or {}).get("rule_config", {}).get("max_points")
    sef_max = (sef_cfg or {}).get("rule_config", {}).get("max_points")
    set_formula = (set_cfg or {}).get("rule_config", {}).get("formula") or DEFAULT_FORMULA
    sef_formula = (sef_cfg or {}).get("rule_config", {}).get("formula") or DEFAULT_FORMULA

    kra = db.session.get(KraConfiguration, criterion.kra_id)
    issues: list[str] = []
    is_official = True
    if kra and kra.guideline_version != OFFICIAL_GUIDELINE_VERSION:
        is_official = False
        issues.append(f"KRA guideline_version is {kra.guideline_version!r}, expected {OFFICIAL_GUIDELINE_VERSION}.")
    if crit_max is not None and int(crit_max) != CRITERION_A_MAX_POINTS:
        is_official = False
    if set_max is not None and int(set_max) != SET_MAX_POINTS:
        is_official = False
    if sef_max is not None and int(sef_max) != SEF_MAX_POINTS:
        is_official = False
    if str(set_formula).strip() != DEFAULT_FORMULA or str(sef_formula).strip() != DEFAULT_FORMULA:
        is_official = False

    label = "official_dbm_ched" if is_official and not issues else "custom_configuration"
    return {
        "configuration_label": label,
        "configuration_label_display": (
            "Official DBM–CHED Scoring" if label == "official_dbm_ched" else "Custom Configuration"
        ),
        "criterion_max_points": crit_max,
        "set_max_points": set_max,
        "sef_max_points": sef_max,
        "set_formula": set_formula,
        "sef_formula": sef_formula,
        "issues": issues,
        "official_defaults": {
            "guideline_version": OFFICIAL_GUIDELINE_VERSION,
            "criterion_max_points": CRITERION_A_MAX_POINTS,
            "set_max_points": SET_MAX_POINTS,
            "sef_max_points": SEF_MAX_POINTS,
            "set_formula": DEFAULT_FORMULA,
            "sef_formula": DEFAULT_FORMULA,
        },
    }


def serialize_scoring_rules_for_admin(criterion_id: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    indicators = (
        KraIndicator.query.filter_by(criterion_id=criterion_id)
        .order_by(KraIndicator.display_order)
        .all()
    )
    profile = configuration_profile()
    for indicator in indicators:
        if indicator.indicator_code not in ALLOWED_INDICATOR_CODES:
            continue
        loaded = load_indicator_scoring(indicator)
        if not loaded:
            continue
        cfg = loaded["rule_config"]
        rows.append(
            {
                "rule_id": loaded["rule_id"],
                "indicator_code": indicator.indicator_code,
                "indicator_name": indicator.indicator_name,
                "rule_name": loaded["rule_name"],
                "rule_type": loaded["rule_type"],
                "guideline_version": loaded["guideline_version"],
                "max_points": cfg.get("max_points"),
                "criterion_max_points": cfg.get("criterion_max_points"),
                "formula": cfg.get("formula") or DEFAULT_FORMULA,
                "locked": False,
                "configuration_label": profile["configuration_label"],
            }
        )
    return rows


def build_rule_snapshot(*, rule: ScoringRule, indicator: KraIndicator, profile: dict[str, Any]) -> dict[str, Any]:
    cfg = rule.rule_config if isinstance(rule.rule_config, dict) else {}
    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "guideline_version": rule.guideline_version,
        "indicator_code": indicator.indicator_code,
        "configuration_label": profile.get("configuration_label"),
        "rule_config": cfg,
    }


def validate_scoring_patch(body: dict) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(body, dict):
        return None, "Invalid request body."
    if body.get("restore_official_defaults"):
        return {"restore_official_defaults": True}, None

    out: dict[str, Any] = {}
    if "criterion_max_points" not in body and "scoring_rules" not in body:
        return {}, None
    if "criterion_max_points" in body:
        try:
            crit = int(body["criterion_max_points"])
        except (TypeError, ValueError):
            return None, "criterion_max_points must be an integer."
        if crit < 1 or crit > MAX_CRITERION_POINTS:
            return None, f"criterion_max_points must be between 1 and {MAX_CRITERION_POINTS}."
        out["criterion_max_points"] = crit

    if "scoring_rules" in body:
        raw = body["scoring_rules"]
        if not isinstance(raw, list) or not raw:
            return None, "Provide one or more scoring_rules to update."
        parsed: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                return None, "Each scoring rule entry must be an object."
            try:
                rule_id = int(item["rule_id"])
            except (KeyError, TypeError, ValueError):
                return None, "Each scoring rule requires rule_id."
            entry: dict[str, Any] = {"rule_id": rule_id}
            if "max_points" in item:
                try:
                    mp = float(item["max_points"])
                except (TypeError, ValueError):
                    return None, "max_points must be a number."
                if mp <= 0 or mp > MAX_INDICATOR_POINTS:
                    return None, f"max_points must be between 0 and {MAX_INDICATOR_POINTS}."
                entry["max_points"] = round(mp, 4)
            if "formula" in item:
                formula, err = validate_formula_expression(str(item["formula"]))
                if err:
                    return None, err
                entry["formula"] = formula
            if "rule_name" in item:
                name = str(item["rule_name"]).strip()
                if not name or len(name) > 200:
                    return None, "rule_name must be 1–200 characters."
                entry["rule_name"] = name
            if len(entry) == 1:
                return None, "Each scoring rule must include max_points, formula, and/or rule_name."
            parsed.append(entry)
        out["scoring_rules"] = parsed

    return out, None


def _sync_criterion_max_on_rules(criterion_id: int, criterion_max: int) -> None:
    indicators = KraIndicator.query.filter_by(criterion_id=criterion_id).all()
    for indicator in indicators:
        if indicator.indicator_code not in ALLOWED_INDICATOR_CODES:
            continue
        rule = _active_rule(indicator.indicator_id)
        if not rule:
            continue
        cfg = dict(rule.rule_config) if isinstance(rule.rule_config, dict) else {}
        cfg["criterion_max_points"] = criterion_max
        rule.rule_config = cfg


def restore_official_defaults(*, admin_user_id: int) -> dict[str, Any]:
    criterion = get_kra_i_criterion_a()
    if not criterion:
        raise ValueError("not_found")
    kra = db.session.get(KraConfiguration, criterion.kra_id)
    if kra:
        kra.guideline_version = OFFICIAL_GUIDELINE_VERSION
    indicators = KraIndicator.query.filter_by(criterion_id=criterion.criterion_id).all()
    before = configuration_profile()
    for indicator in indicators:
        if indicator.indicator_code not in ALLOWED_INDICATOR_CODES:
            continue
        rule = _active_rule(indicator.indicator_id)
        if not rule:
            rule = ScoringRule(
                indicator_id=indicator.indicator_id,
                rule_name=_official_rule_name(indicator.indicator_code),
                rule_type="percentage_of_max",
                rule_config=official_rule_config(indicator_code=indicator.indicator_code),
                guideline_version=OFFICIAL_GUIDELINE_VERSION,
                is_active=True,
            )
            db.session.add(rule)
            continue
        rule.rule_name = _official_rule_name(indicator.indicator_code)
        rule.rule_type = "percentage_of_max"
        rule.rule_config = official_rule_config(indicator_code=indicator.indicator_code)
        rule.guideline_version = OFFICIAL_GUIDELINE_VERSION
        rule.is_active = True
    db.session.flush()
    after = configuration_profile()
    _append_scoring_audit(admin_user_id=admin_user_id, criterion_id=criterion.criterion_id, before=before, after=after)
    return after


def apply_scoring_updates(*, updates: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    if updates.get("restore_official_defaults"):
        return restore_official_defaults(admin_user_id=admin_user_id)

    criterion = get_kra_i_criterion_a()
    if not criterion:
        raise ValueError("not_found")
    before = configuration_profile()

    if "criterion_max_points" in updates:
        _sync_criterion_max_on_rules(criterion.criterion_id, updates["criterion_max_points"])

    if "scoring_rules" in updates:
        allowed_rules = {
            rule.rule_id: (rule, ind)
            for ind in KraIndicator.query.filter_by(criterion_id=criterion.criterion_id).all()
            if ind.indicator_code in ALLOWED_INDICATOR_CODES
            for rule in ScoringRule.query.filter_by(indicator_id=ind.indicator_id, is_active=True).all()
        }
        set_max = None
        sef_max = None
        crit_max = updates.get("criterion_max_points")
        for item in updates["scoring_rules"]:
            pair = allowed_rules.get(item["rule_id"])
            if not pair:
                raise ValueError("rule_scope")
            rule, indicator = pair
            cfg = dict(rule.rule_config) if isinstance(rule.rule_config, dict) else {}
            if crit_max is not None:
                cfg["criterion_max_points"] = crit_max
            elif "criterion_max_points" not in cfg:
                cfg["criterion_max_points"] = CRITERION_A_MAX_POINTS
            if "max_points" in item:
                cfg["max_points"] = item["max_points"]
            if "formula" in item:
                cfg["formula"] = item["formula"]
            rule.rule_config = cfg
            if "rule_name" in item:
                rule.rule_name = item["rule_name"]
            if indicator.indicator_code == "A.1":
                set_max = float(cfg.get("max_points") or 0)
            if indicator.indicator_code == "A.2":
                sef_max = float(cfg.get("max_points") or 0)

        if crit_max is None:
            for _, indicator in allowed_rules.values():
                rule = _active_rule(indicator.indicator_id)
                if rule and isinstance(rule.rule_config, dict):
                    crit_max = rule.rule_config.get("criterion_max_points")
                    if crit_max is not None:
                        break
        if crit_max is not None and set_max is not None and sef_max is not None:
            if set_max + sef_max > float(crit_max) + 0.0001:
                raise ValueError("points_consistency")

    db.session.flush()
    after = configuration_profile()
    _append_scoring_audit(admin_user_id=admin_user_id, criterion_id=criterion.criterion_id, before=before, after=after)
    return after


def _append_scoring_audit(*, admin_user_id: int, criterion_id: int, before: dict, after: dict) -> None:
    db.session.execute(
        text(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (:user_id, :action, :entity_type, :entity_id, CAST(:details AS jsonb))
            """
        ),
        {
            "user_id": admin_user_id,
            "action": "kra_i_criterion_a_scoring_update",
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
