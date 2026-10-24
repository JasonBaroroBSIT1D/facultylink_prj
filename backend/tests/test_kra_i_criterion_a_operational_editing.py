"""Admin Validation & Scoring — KRA I Criterion A OCR thresholds."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.kra_configuration import KraCriterionOperationalSettings, ScoringRule  # noqa: E402
from models.kra_configuration import KraIndicator  # noqa: E402
from services.kra_i_criterion_a_operational import OFFICIAL_GUIDELINE_VERSION  # noqa: E402
from services.validation.rule_loader import load_set_sef_rules  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf, _login, _persist_web_cookie  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402
from tests.test_kra_configuration_api import _clear_kra_tables  # noqa: E402
from tests.test_kra_i_criterion_a_metadata_editing import _seed_kra_i_criterion_a  # noqa: E402


def test_validation_scoring_payload_and_locked_scoring():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()

    _admin_cookie(client)
    resp = client.get("/api/v1/admin/validation-scoring/kra-i/criterion-a")
    assert resp.status_code == 200
    op = resp.get_json()["operational"]
    assert op["criterion_code"] == "A"
    assert op["locked_official"]["criterion_max_points"] == 60
    assert op["locked_official"]["set_max_points"] == 36
    assert op["locked_official"]["sef_max_points"] == 24
    assert op["locked_official"]["guideline_version"] == OFFICIAL_GUIDELINE_VERSION
    assert op["locked_scoring_issues"] == []
    assert op["confidence_thresholds"]["field_min"] == 0.6

    admin_kra = client.get("/api/v1/admin/kra-configuration").get_json()
    assert "kra_i_criterion_a_operational" not in admin_kra
    assert admin_kra["kra_i_criterion_a_editing"] is not None

    public = client.get("/api/v1/kra-configuration")
    assert "kra_i_criterion_a_editing" not in public.get_json()

    with app.app_context():
        _clear_kra_tables()


def test_admin_patch_persists_and_validation_engine_reads():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        criterion_id, _, _, _ = _seed_kra_i_criterion_a()

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    patch = client.patch(
        "/api/v1/admin/validation-scoring/kra-i/criterion-a/operational-settings",
        json={"confidence_thresholds": {"field_min": 0.72, "ocr_mean_min": 0.4}},
        headers={"X-CSRF-Token": csrf},
    )
    assert patch.status_code == 200, patch.get_json()
    body = patch.get_json()["operational"]
    assert body["confidence_thresholds"]["field_min"] == 0.72

    reload = client.get("/api/v1/admin/validation-scoring/kra-i/criterion-a")
    assert reload.get_json()["operational"]["confidence_thresholds"]["field_min"] == 0.72

    with app.app_context():
        rules = load_set_sef_rules()
        assert rules["confidence_thresholds"]["field_min"] == 0.72
        row = db.session.get(KraCriterionOperationalSettings, criterion_id)
        assert row is not None
        audit = db.session.execute(
            text(
                """
                SELECT action FROM audit_logs
                WHERE entity_type = 'kra_criterion_operational_settings'
                  AND entity_id = :cid
                ORDER BY audit_id DESC LIMIT 1
                """
            ),
            {"cid": str(criterion_id)},
        ).fetchone()
        assert audit[0] == "kra_i_criterion_a_operational_update"

    with app.app_context():
        _clear_kra_tables()


def test_rejects_invalid_and_unauthorized():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()

    reviewer = app.test_client()
    res = _login(reviewer, "reviewer@facultylink.edu", "demo-reviewer")
    _persist_web_cookie(reviewer, res)
    csrf = _fetch_csrf(reviewer)
    denied = reviewer.patch(
        "/api/v1/admin/validation-scoring/kra-i/criterion-a/operational-settings",
        json={"confidence_thresholds": {"field_min": 0.7}},
        headers={"X-CSRF-Token": csrf},
    )
    assert denied.status_code == 403

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    bad_identity = client.patch(
        "/api/v1/admin/validation-scoring/kra-i/criterion-a/operational-settings",
        json={"confidence_thresholds": {"identity_min": 0.2}},
        headers={"X-CSRF-Token": csrf},
    )
    assert bad_identity.status_code == 400

    with app.app_context():
        _clear_kra_tables()


def test_locked_scoring_mismatch_surfaces_in_validation_payload():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        _seed_kra_i_criterion_a()
        rule = ScoringRule.query.join(KraIndicator).filter(KraIndicator.indicator_code == "A.1").first()
        rule.rule_config = {**rule.rule_config, "max_points": 99}
        db.session.commit()

    _admin_cookie(client)
    op = client.get("/api/v1/admin/validation-scoring/kra-i/criterion-a").get_json()["operational"]
    assert any("SET max_points" in issue for issue in op["locked_scoring_issues"])

    with app.app_context():
        _clear_kra_tables()
