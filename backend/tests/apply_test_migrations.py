"""Apply pending SQL migrations on the isolated test database only."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.apply_phase1_documents_migration import _conninfo_from_env, apply, pending_migrations  # noqa: E402
from scripts.apply_reviewer_assignment_policy_migration import _index_exists  # noqa: E402

import psycopg  # noqa: E402

MIGRATION_004 = ROOT / "backend" / "migrations" / "004_one_active_reviewer_per_faculty.sql"
MIGRATION_005 = ROOT / "backend" / "migrations" / "005_kra_i_criterion_a_operational_settings.sql"


def _db_name_from_test_uri(uri: str) -> str:
    parsed = urlparse(uri.replace("postgresql+psycopg", "postgresql"))
    path = (parsed.path or "").lstrip("/")
    if not path:
        raise RuntimeError("TEST_DATABASE_URL must include a database name.")
    return path


def _apply_migration_004_on_test_db(conninfo: str) -> None:
    if not MIGRATION_004.is_file():
        return
    with psycopg.connect(conninfo) as conn:
        if _index_exists(conn):
            return
        conn.execute(MIGRATION_004.read_text(encoding="utf-8"))
        conn.commit()


def _operational_settings_table_exists(conn: psycopg.Connection) -> bool:
    return bool(
        conn.execute(
            "SELECT to_regclass('public.kra_criterion_operational_settings') IS NOT NULL"
        ).fetchone()[0]
    )


def _apply_migration_005_on_test_db(conninfo: str) -> None:
    if not MIGRATION_005.is_file():
        return
    with psycopg.connect(conninfo) as conn:
        if _operational_settings_table_exists(conn):
            return
        conn.execute(MIGRATION_005.read_text(encoding="utf-8"))
        conn.commit()


def apply_phase1_on_test_db(test_database_uri: str) -> None:
    from testing_db_guard import validate_test_database_uri

    validate_test_database_uri(test_database_uri)
    db_name = _db_name_from_test_uri(test_database_uri)
    conninfo = _conninfo_from_env(db_name)
    with psycopg.connect(conninfo) as conn:
        phase1_pending = pending_migrations(conn)
    if phase1_pending:
        apply(conninfo, dry_run=False)
    _apply_migration_004_on_test_db(conninfo)
    _apply_migration_005_on_test_db(conninfo)


def apply_phase1_on_test_db_from_env() -> None:
    uri = (os.getenv("TEST_DATABASE_URL") or "").strip()
    if not uri:
        return
    apply_phase1_on_test_db(uri)
