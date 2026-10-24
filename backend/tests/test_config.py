"""Shared pytest Flask config — isolated PostgreSQL only."""
from __future__ import annotations

from config import Config

from testing_db_guard import resolve_test_database_uri

# Resolved once when pytest loads this module (after conftest pytest_configure).
TEST_DATABASE_URI = resolve_test_database_uri()


class IsolatedTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URI
    MAIL_SUPPRESS_SEND = True


class EmailTestConfig(IsolatedTestConfig):
    """Same isolated DB; email sending suppressed via mailer."""

    pass
