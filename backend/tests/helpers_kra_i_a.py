"""Seed KRA I Criterion A with SET/SEF indicators on isolated test DB."""
from __future__ import annotations

from extensions import db
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule
from services.kra_i_criterion_a_operational import OFFICIAL_GUIDELINE_VERSION
from services.kra_i_criterion_a_scoring import official_rule_config, _official_rule_name


def seed_kra_i_criterion_a_set_sef() -> tuple[int, int, int]:
    """Returns (criterion_id, set_indicator_id, sef_indicator_id)."""
    kra = KraConfiguration.query.filter_by(kra_code="KRA I").first()
    if not kra:
        kra = KraConfiguration(
            kra_code="KRA I",
            kra_name="Instruction",
            guideline_version="DBM-CHED-JC-01-2026-test",
            is_active=True,
        )
        db.session.add(kra)
        db.session.flush()

    criterion = KraCriterion.query.filter_by(kra_id=kra.kra_id, criterion_code="A").first()
    if not criterion:
        criterion = KraCriterion(
            kra_id=kra.kra_id,
            criterion_code="A",
            criterion_name="Teaching Effectiveness",
            display_order=1,
        )
        db.session.add(criterion)
        db.session.flush()

    def _indicator(code: str, name: str, order: int) -> KraIndicator:
        row = KraIndicator.query.filter_by(criterion_id=criterion.criterion_id, indicator_code=code).first()
        if row:
            return row
        row = KraIndicator(
            criterion_id=criterion.criterion_id,
            indicator_code=code,
            indicator_name=name,
            credit_uniqueness="one_active_credit_per_term",
            display_order=order,
        )
        db.session.add(row)
        db.session.flush()
        return row

    set_ind = _indicator("A.1", "Student Evaluation of Teachers", 1)
    sef_ind = _indicator("A.2", "Supervisor's Evaluation of Faculty", 2)

    for ind in (set_ind, sef_ind):
        existing = ScoringRule.query.filter_by(indicator_id=ind.indicator_id, is_active=True).first()
        if not existing:
            db.session.add(
                ScoringRule(
                    indicator_id=ind.indicator_id,
                    rule_name=_official_rule_name(ind.indicator_code),
                    rule_type="percentage_of_max",
                    rule_config=official_rule_config(indicator_code=ind.indicator_code),
                    guideline_version=OFFICIAL_GUIDELINE_VERSION,
                    is_active=True,
                )
            )
    db.session.commit()
    return criterion.criterion_id, set_ind.indicator_id, sef_ind.indicator_id
