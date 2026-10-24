"""Read-only KRA configuration API."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from tests.test_config import IsolatedTestConfig as TestConfig  # noqa: E402
from extensions import db  # noqa: E402
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator, ScoringRule  # noqa: E402
from tests.test_auth_api import _admin_cookie, _fetch_csrf  # noqa: E402


def _clear_kra_tables():
    db.session.query(ScoringRule).delete()
    db.session.query(KraIndicator).delete()
    db.session.query(KraCriterion).delete()
    db.session.query(KraConfiguration).delete()
    db.session.commit()


def test_admin_kra_configuration_empty():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    resp = client.get(
        "/api/v1/admin/kra-configuration",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kras"] == []
    assert body.get("guideline_version") is None


def test_admin_kra_configuration_serializes_tree():
    app = create_app(TestConfig)
    client = app.test_client()
    with app.app_context():
        _clear_kra_tables()
        kra = KraConfiguration(
            kra_code="KRA I",
            kra_name="Instruction",
            guideline_version="demo-v1",
            is_active=True,
        )
        criterion = KraCriterion(
            kra=kra,
            criterion_code="A",
            criterion_name="Teaching load",
            display_order=1,
        )
        indicator = KraIndicator(
            criterion=criterion,
            indicator_code="A.1",
            indicator_name="Hours taught",
            required_evidence="Class schedule",
            display_order=1,
        )
        rule = ScoringRule(
            indicator=indicator,
            rule_name="Points per hour",
            rule_type="linear",
            rule_config={"max_points": 10},
            guideline_version="demo-v1",
            is_active=True,
        )
        db.session.add_all([kra, criterion, indicator, rule])
        db.session.commit()

    _admin_cookie(client)
    csrf = _fetch_csrf(client)
    resp = client.get(
        "/api/v1/admin/kra-configuration",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["guideline_version"] == "demo-v1"
    assert len(body["kras"]) == 1
    kra_payload = body["kras"][0]
    assert kra_payload["code"] == "KRA I"
    assert kra_payload["criteria_count"] == 1
    ind = kra_payload["criteria"][0]["indicators"][0]
    assert ind["code"] == "A.1"
    assert ind["scoring_rules"][0]["max_points"] == 10

    with app.app_context():
        _clear_kra_tables()
