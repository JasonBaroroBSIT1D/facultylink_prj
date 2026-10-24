"""Refuse automated tests against development or production PostgreSQL databases."""
from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

FORBIDDEN_DATABASE_NAMES = frozenset({"facultylink_db", "postgres", "template0", "template1"})


def database_name_from_uri(database_uri: str) -> str:
    uri = (database_uri or "").strip()
    if uri.startswith("postgresql+"):
        uri = "postgresql://" + uri.split("://", 1)[1]
    parsed = urlparse(uri)
    name = (parsed.path or "").lstrip("/")
    if not name:
        return ""
    return unquote(name.split("?")[0])


def development_database_name() -> str:
    dev_uri = (os.getenv("DATABASE_URL") or "").strip()
    if dev_uri:
        return database_name_from_uri(dev_uri).lower()
    return (os.getenv("DB_NAME") or "facultylink_db").strip().lower()


def validate_test_database_uri(database_uri: str) -> None:
    if not database_uri or not database_uri.strip():
        raise RuntimeError(
            "TEST_DATABASE_URL is required for pytest. "
            "Example: postgresql+psycopg://postgres:@localhost:5432/facultylink_test_db"
        )
    db_name = database_name_from_uri(database_uri).lower()
    if not db_name:
        raise RuntimeError("TEST_DATABASE_URL must include a database name.")
    if db_name in FORBIDDEN_DATABASE_NAMES:
        raise RuntimeError(
            f"Refusing to run tests against forbidden database '{db_name}'. "
            "Use a dedicated test database such as facultylink_test_db via TEST_DATABASE_URL."
        )
    if db_name == development_database_name():
        raise RuntimeError(
            "TEST_DATABASE_URL must not point to the same database as development (DATABASE_URL / DB_NAME)."
        )


def assert_testing_uses_isolated_database(testing: bool, database_uri: str) -> None:
    if not testing:
        return
    validate_test_database_uri(database_uri)


def resolve_test_database_uri() -> str:
    uri = (os.getenv("TEST_DATABASE_URL") or "").strip()
    validate_test_database_uri(uri)
    return uri
