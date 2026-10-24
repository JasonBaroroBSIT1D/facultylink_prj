"""Unit tests for database isolation guard (no DB connection)."""
from __future__ import annotations

import os

import pytest

from testing_db_guard import database_name_from_uri, validate_test_database_uri


def test_database_name_from_uri():
    assert database_name_from_uri("postgresql+psycopg://u:p@localhost:5432/facultylink_test_db") == "facultylink_test_db"


def test_rejects_facultylink_db(monkeypatch):
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+psycopg://localhost/facultylink_db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_NAME", "facultylink_test_db")
    with pytest.raises(RuntimeError, match="forbidden"):
        validate_test_database_uri(os.environ["TEST_DATABASE_URL"])
