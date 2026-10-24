"""Apply migration 005 (KRA I Criterion A operational settings table). Approval required on facultylink_db."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend" / "migrations" / "005_kra_i_criterion_a_operational_settings.sql"


def _conninfo(db_name: str) -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={db_name} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def _table_exists(conn: psycopg.Connection) -> bool:
    return bool(
        conn.execute(
            "SELECT to_regclass('public.kra_criterion_operational_settings') IS NOT NULL"
        ).fetchone()[0]
    )


def apply(conninfo: str, *, dry_run: bool) -> int:
    if not MIGRATION.is_file():
        print("Missing migration file.", file=sys.stderr)
        return 1
    with psycopg.connect(conninfo) as conn:
        if _table_exists(conn):
            print("Migration 005 already applied.")
            return 0
        sql = MIGRATION.read_text(encoding="utf-8")
        if dry_run:
            print("Dry run — would execute:\n")
            print(sql)
            print("\nBackup: python backend/scripts/backup_facultylink_db.py")
            print("Rollback: DROP TABLE IF EXISTS kra_criterion_operational_settings;")
            return 0
        conn.execute(sql)
        conn.commit()
        print("Applied 005_kra_i_criterion_a_operational_settings.sql")
    return 0


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=os.getenv("DB_NAME", "facultylink_db"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return apply(_conninfo(args.database), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
