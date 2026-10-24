"""Post-validation scoring, crediting, and system approval for KRA I Criterion A SET/SEF."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select, text
from extensions import db
from models.document import Document
from models.document_score_contribution import DocumentScoreContribution
from models.kra_configuration import KraConfiguration, KraIndicator
from models.user import User
from services.credit_uniqueness import ONE_ACTIVE_CREDIT_PER_TERM, build_credit_uniqueness_key
from services.kra_i_criterion_a_scoring import (
    build_rule_snapshot,
    calculate_points_from_rule,
    configuration_profile,
    load_indicator_scoring,
)
from services.validation.set_sef_engine import ValidationOutcome


def _append_audit(document_id: int, user_id: int, action: str, details: dict) -> None:
    db.session.execute(
        text(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (:user_id, :action, 'document', :entity_id, CAST(:details AS jsonb))
            """
        ),
        {
            "user_id": user_id,
            "action": action,
            "entity_id": str(document_id),
            "details": json.dumps(details),
        },
    )


def _active_credit_exists(credit_key: str) -> bool:
    row = db.session.scalar(
        select(DocumentScoreContribution.contribution_id).where(
            DocumentScoreContribution.credit_uniqueness_key == credit_key,
            DocumentScoreContribution.credit_state == "credited",
        )
    )
    return row is not None


def _rating_from_outcome(outcome: ValidationOutcome, indicator_code: str | None) -> float | None:
    fields = outcome.extracted_fields or {}
    if indicator_code == "A.1":
        val = fields.get("overall_set_rating", fields.get("overall_rating"))
    elif indicator_code == "A.2":
        val = fields.get("overall_sef_rating", fields.get("overall_rating"))
    else:
        val = fields.get("overall_rating")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _duplicate_check_failed(outcome: ValidationOutcome) -> bool:
    return any(c.name == "duplicate_semester_evidence" and not c.passed for c in outcome.checks)


def finalize_criterion_a_set_sef(
    *,
    document: Document,
    faculty_user: User,
    outcome: ValidationOutcome,
    rules_json: dict,
) -> dict:
    """Apply scoring ledger row and set document status (system_approved or needs_verification)."""
    profile = configuration_profile()
    summary: dict = {
        "document_status": document.status,
        "system_decision": None,
        "system_calculated_points": 0.0,
        "credited_points": 0.0,
        "provisional_points": 0.0,
        "contribution_id": None,
    }

    indicator = None
    if outcome.classified_indicator_id:
        indicator = db.session.get(KraIndicator, outcome.classified_indicator_id)
    if not indicator:
        document.status = "needs_verification"
        summary["document_status"] = document.status
        summary["system_decision"] = "manual_review_required"
        return summary

    loaded = load_indicator_scoring(indicator)
    rating = _rating_from_outcome(outcome, indicator.indicator_code)
    provisional = 0.0
    if loaded and rating is not None:
        provisional = calculate_points_from_rule(rating=rating, rule_config=loaded["rule_config"])

    duplicate_blocked = _duplicate_check_failed(outcome)
    auto_eligible = outcome.result == "passed" and not duplicate_blocked and loaded and rating is not None

    kra_id = None
    if document.criterion_id:
        from models.kra_configuration import KraCriterion

        crit = db.session.get(KraCriterion, document.criterion_id)
        if crit:
            kra_id = crit.kra_id

    academic_year = str(outcome.extracted_fields.get("academic_year") or "")
    semester = str(outcome.extracted_fields.get("semester") or "")
    if not academic_year or not semester:
        auto_eligible = False

    mode = indicator.credit_uniqueness or ONE_ACTIVE_CREDIT_PER_TERM
    credit_key = None
    if academic_year and semester:
        credit_key = build_credit_uniqueness_key(
            mode=mode,
            faculty_id=document.faculty_id,
            indicator_id=indicator.indicator_id,
            academic_year=academic_year,
            semester=semester,
            evidence_sha256=document.sha256_hash,
        )

    if auto_eligible and credit_key and _active_credit_exists(credit_key):
        auto_eligible = False
        duplicate_blocked = True

    credited = 0.0
    credit_state = "none"
    system_decision = "manual_review_required"
    credited_at = None

    if auto_eligible:
        document.status = "system_approved"
        credited = provisional
        credit_state = "credited"
        system_decision = "auto_approved"
        credited_at = datetime.now(timezone.utc)
    else:
        document.status = "needs_verification"

    summary.update(
        {
            "document_status": document.status,
            "system_decision": system_decision,
            "system_calculated_points": provisional,
            "provisional_points": provisional if document.status == "needs_verification" else 0.0,
            "credited_points": credited,
        }
    )

    if not loaded:
        _append_audit(
            document.document_id,
            faculty_user.user_id,
            "document.scoring_skipped",
            {"reason": "missing_scoring_rule", **summary},
        )
        return summary

    from models.kra_configuration import ScoringRule

    rule = db.session.get(ScoringRule, loaded["rule_id"])
    snapshot = build_rule_snapshot(rule=rule, indicator=indicator, profile=profile) if rule else {}
    snapshot["validation_result"] = outcome.result
    snapshot["section_10_flags"] = rules_json.get("section_10_unverified_flags")
    snapshot["rating_used"] = rating

    contribution = DocumentScoreContribution(
        document_id=document.document_id,
        faculty_id=document.faculty_id,
        kra_id=kra_id,
        indicator_id=indicator.indicator_id,
        period_id=document.period_id,
        academic_year=academic_year or "unknown",
        semester=semester or "unknown",
        evidence_sha256=document.sha256_hash,
        credit_uniqueness_mode=mode,
        credit_uniqueness_key=credit_key,
        guideline_version=loaded.get("guideline_version"),
        rule_snapshot=snapshot,
        system_calculated_points=provisional,
        provisional_points=provisional if credit_state == "none" else 0.0,
        credited_points=credited,
        credit_state=credit_state,
        system_decision=system_decision,
        credited_at=credited_at,
    )
    db.session.add(contribution)
    db.session.flush()

    summary["contribution_id"] = contribution.contribution_id
    _append_audit(
        document.document_id,
        faculty_user.user_id,
        "document.system_scoring_completed",
        {
            **summary,
            "indicator_code": indicator.indicator_code,
            "configuration_label": profile.get("configuration_label"),
            "duplicate_blocked": duplicate_blocked,
        },
    )
    return summary
