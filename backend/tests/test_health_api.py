"""Phase 4.2 API smoke tests (requires isolated TEST_DATABASE_URL)."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from tests.test_config import IsolatedTestConfig  # noqa: E402


def test_health_ok():
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.get_json()
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "FacultyLink API"
    assert data["database"] == "connected"
    auth = data.get("auth_onboarding") or {}
    assert auth.get("mode") == "temporary_password"
    assert auth.get("invitation_setup_codes") is False


def test_unknown_route_404():
    app = create_app(IsolatedTestConfig)
    client = app.test_client()
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "not_found"


if __name__ == "__main__":
    test_health_ok()
    test_unknown_route_404()
    print("All Phase 4.2 API tests passed.")
