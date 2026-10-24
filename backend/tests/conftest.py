"""Pytest configuration: isolated DB guard, test DB seeding, shared fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def pytest_configure(config):  # noqa: ARG001
    """Block collection unless TEST_DATABASE_URL is safe and set."""
    from testing_db_guard import validate_test_database_uri

    uri = (os.getenv("TEST_DATABASE_URL") or "").strip()
    try:
        validate_test_database_uri(uri)
    except RuntimeError as exc:
        raise pytest.UsageError(str(exc)) from exc
    # Prevent accidental use of dev DB URI in tests even if import order varies.
    os.environ["FACULTYLINK_PYTEST_ACTIVE"] = "1"


def pytest_sessionstart(session):  # noqa: ARG001
    from app import create_app
    from tests.apply_test_migrations import apply_phase1_on_test_db_from_env
    from tests.seed_test_accounts import seed_test_demo_accounts
    from tests.test_config import IsolatedTestConfig

    apply_phase1_on_test_db_from_env()
    app = create_app(IsolatedTestConfig)
    with app.app_context():
        seed_test_demo_accounts()


@pytest.fixture
def test_app():
    from app import create_app
    from tests.test_config import IsolatedTestConfig

    app = create_app(IsolatedTestConfig)
    yield app


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()
