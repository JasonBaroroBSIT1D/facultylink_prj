"""Apply migration 004 (one active reviewer per faculty). Requires backup + approval on facultylink_db."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend" / "migrations" / "004_one_active_reviewer_per_faculty.sql"


def _conninfo(db_name: str) -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={db_name} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def _index_exists(conn: psycopg.Connection) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname = 'uq_reviewer_assignments_one_active_per_faculty'
        """
    ).fetchone()
    return bool(row)


def apply(conninfo: str, *, dry_run: bool) -> int:
    if not MIGRATION.is_file():
        print("Missing migration file.", file=sys.stderr)
        return 1
    with psycopg.connect(conninfo) as conn:
        if _index_exists(conn):
            print("Migration 004 already applied (partial unique index present).")
            return 0
        sql = MIGRATION.read_text(encoding="utf-8")
        if dry_run:
            print("Dry run — would execute:\n")
            print(sql)
            print("\nBackup first: python backend/scripts/backup_facultylink_db.py")
            print("Rollback: DROP INDEX IF EXISTS uq_reviewer_assignments_one_active_per_faculty;")
            print("         (Re-activate rows manually from backup if needed.)")
            return 0
        conn.execute(sql)
        conn.commit()
        print("Applied 004_one_active_reviewer_per_faculty.sql")
    return 0


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Apply reviewer assignment policy migration 004.")
    parser.add_argument("--database", default=os.getenv("DB_NAME", "facultylink_db"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return apply(_conninfo(args.database), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
