"""Admin KRA I Criterion A metadata and evidence editing."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.kra_configuration import (  # noqa: E402
    KraConfiguration,
    KraCriterion,
    KraIndicator,
    ScoringRule,
)
from services.kra_i_criterion_a_operational import (  # noqa: E402
    CRITERION_A_MAX_POINTS,
    OFFICIAL_GUIDELINE_VERSION,
    SEF_MAX_POINTS,
    SET_MAX_POINTS,
)
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402
from tests.test_kra_configuration_api import _clear_kra_tables  # noqa: E402


def _seed_kra_i_criterion_a():
    kra = KraConfiguration(
        kra_code="KRA I",
        kra_name="Instruction",
        guideline_version=OFFICIAL_GUIDELINE_VERSION,
        is_active=True,
    )
    criterion = KraCriterion(
        kra=kra,
        criterion_code="A",
        criterion_name="Teaching Effectiveness",
        description="Original description",
        display_order=1,
    )
    set_ind = KraIndicator(
        criterion=criterion,
        indicator_code="A.1",
        indicator_name="Student Evaluation of Teachers",
        required_evidence="SET evidence original",
        display_order=1,
    )
    sef_ind = KraIndicator(
        criterion=criterion,
        indicator_code="A.2",
        indicator_name="Supervisor's Evaluation of Faculty",
        required_evidence="SEF evidence original",
        display_order=2,
    )
    set_rule = ScoringRule(
        indicator=set_ind,
        rule_name="SET — (Overall SET Rating / 100) × 36",
        rule_type="percentage_of_max",
        rule_config={"max_points": SET_MAX_POINTS, "criterion_max_points": CRITERION_A_MAX_POINTS},
        guideline_version=OFFICIAL_GUIDELINE_VERSION,
        is_active=True,
    )
    sef_rule = ScoringRule(
        indicator=sef_ind,
        rule_name="SEF — (Overall SEF Rating / 100) × 24",
        rule_type="percentage_of_max",
        rule_config={"max_points": SEF_MAX_POINTS, "criterion_max_points": CRITERION_A_MAX_POINTS},
        guideline_version=OFFICIAL_GUIDELINE_VERSION,
        is_active=True,
    )
    db.session.add_all([kra, criterion, set_ind, sef_ind, set_rule, sef_rule])
    db.session.commit()
    return criterion.criterion_id, set_ind.indicator_id, sef_ind.indicator_id, set_rule.rule_id


def test_admin_editing_payload_shows_locked_rules():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()

    _admin_cookie(client)
    body = client.get("/api/v1/admin/kra-configuration").get_json()
    editing = body["kra_i_criterion_a_editing"]
    assert editing["criterion_name"] == "Teaching Effectiveness"
    assert len(editing["scoring_rules_locked"]) == 2
    assert editing["scoring_rules_locked"][0]["locked"] is False
    assert editing["configuration_profile"]["configuration_label"] == "official_dbm_ched"
    assert editing["locked_official"]["criterion_max_points"] == 60

    mobile = client.get("/api/v1/kra-configuration")
    assert mobile.status_code == 200
    assert "kra_i_criterion_a_editing" not in mobile.get_json()

    with app.app_context():
        _clear_kra_tables()


def test_metadata_patch_persists_and_audit():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()
        set_id = KraIndicator.query.filter_by(indicator_code="A.1").first().indicator_id
        sef_id = KraIndicator.query.filter_by(indicator_code="A.2").first().indicator_id
        set_rule_id = ScoringRule.query.filter_by(indicator_id=set_id).first().rule_id

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    patch = client.patch(
        "/api/v1/admin/kra-configuration/kra-i/criterion-a",
        json={
            "criterion_name": "Teaching Effectiveness (updated)",
            "description": "Updated criterion description",
            "indicators": [
                {"indicator_id": set_id, "indicator_name": "SET updated", "required_evidence": "SET ev updated"},
                {"indicator_id": sef_id, "required_evidence": "SEF ev updated"},
            ],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert patch.status_code == 200, patch.get_json()
    editing = patch.get_json()["kra_i_criterion_a_editing"]
    assert editing["criterion_name"] == "Teaching Effectiveness (updated)"
    set_row = next(i for i in editing["indicators"] if i["code"] == "A.1")
    assert set_row["required_evidence"] == "SET ev updated"

    reload = client.get("/api/v1/admin/kra-configuration").get_json()
    crit = reload["kras"][0]["criteria"][0]
    assert crit["name"] == "Teaching Effectiveness (updated)"
    assert crit["indicators"][0]["required_evidence"] == "SET ev updated"

    with app.app_context():
        rule = db.session.get(ScoringRule, set_rule_id)
        assert int(rule.rule_config["max_points"]) == SET_MAX_POINTS
        audit = db.session.execute(
            text(
                """
                SELECT action FROM audit_logs
                WHERE action = 'kra_i_criterion_a_metadata_update'
                ORDER BY audit_id DESC LIMIT 1
                """
            )
        ).fetchone()
        assert audit is not None

    with app.app_context():
        _clear_kra_tables()


def test_metadata_patch_accepts_scoring_rules_and_marks_custom():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()
        set_id = KraIndicator.query.filter_by(indicator_code="A.1").first().indicator_id
        set_rule_id = ScoringRule.query.filter_by(indicator_id=set_id).first().rule_id

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    patch = client.patch(
        "/api/v1/admin/kra-configuration/kra-i/criterion-a",
        json={
            "criterion_max_points": 60,
            "scoring_rules": [{"rule_id": set_rule_id, "max_points": 30, "formula": "(rating / 100) * max_points"}],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert patch.status_code == 200, patch.get_json()
    editing = patch.get_json()["kra_i_criterion_a_editing"]
    assert editing["configuration_profile"]["configuration_label"] == "custom_configuration"
    set_rule = next(r for r in editing["scoring_rules"] if r["indicator_code"] == "A.1")
    assert float(set_rule["max_points"]) == 30

    with app.app_context():
        _clear_kra_tables()


def test_metadata_patch_rejects_invalid_scoring_and_non_admin():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()

    reviewer = app.test_client()
    res = _login(reviewer, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(reviewer, res)
    csrf = _fetch_csrf(reviewer)
    assert (
        reviewer.patch(
            "/api/v1/admin/kra-configuration/kra-i/criterion-a",
            json={"criterion_name": "X"},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 403
    )

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    bad = client.patch(
        "/api/v1/admin/kra-configuration/kra-i/criterion-a",
        json={"criterion_name": "OK", "max_points": 99},
        headers={"X-CSRF-Token": csrf},
    )
    assert bad.status_code == 400

    set_rule_id = None
    with app.app_context():
        set_id = KraIndicator.query.filter_by(indicator_code="A.1").first().indicator_id
        set_rule_id = ScoringRule.query.filter_by(indicator_id=set_id).first().rule_id
    bad_formula = client.patch(
        "/api/v1/admin/kra-configuration/kra-i/criterion-a",
        json={"scoring_rules": [{"rule_id": set_rule_id, "formula": "__import__('os')"}]},
        headers={"X-CSRF-Token": csrf},
    )
    assert bad_formula.status_code == 400

    with app.app_context():
        _clear_kra_tables()
