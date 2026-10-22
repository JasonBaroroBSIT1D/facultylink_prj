"""Phase 4.2 API smoke tests (requires PostgreSQL facultylink_db)."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402


def test_health_ok():
    app = create_app()
    client = app.test_client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.get_json()
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "FacultyLink API"
    assert data["database"] == "connected"


def test_unknown_route_404():
    app = create_app()
    client = app.test_client()
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "not_found"


if __name__ == "__main__":
    test_health_ok()
    test_unknown_route_404()
    print("All Phase 4.2 API tests passed.")
