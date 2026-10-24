"""Apply Phase 1 document migrations (002 foundation + 003 credit-uniqueness patch)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_002 = ROOT / "backend" / "migrations" / "002_phase1_documents_foundation.sql"
MIGRATION_003 = ROOT / "backend" / "migrations" / "003_phase1_credit_uniqueness_adjustment.sql"


def _conninfo_from_env(db_name: str | None = None) -> str:
    name = db_name or os.getenv("DB_NAME", "facultylink_db")
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={name} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def _ledger_exists(conn: psycopg.Connection) -> bool:
    return conn.execute(
        "SELECT to_regclass('public.document_score_contributions') IS NOT NULL"
    ).fetchone()[0]


def _credit_slot_column_exists(conn: psycopg.Connection) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'document_score_contributions'
          AND column_name = 'credit_uniqueness_key'
        """
    ).fetchone()
    return bool(row)


def pending_migrations(conn: psycopg.Connection) -> list[Path]:
    pending: list[Path] = []
    if not _ledger_exists(conn):
        pending.append(MIGRATION_002)
    elif not _credit_slot_column_exists(conn):
        pending.append(MIGRATION_003)
    return pending


def apply(conninfo: str, dry_run: bool = False) -> int:
    if not MIGRATION_002.is_file():
        print("Migration file missing.", file=sys.stderr)
        return 1
    with psycopg.connect(conninfo) as conn:
        todo = pending_migrations(conn)
        if not todo:
            print("Phase 1 document migrations already up to date.")
            return 0
        if dry_run:
            for path in todo:
                print(f"Dry run: would apply {path.name}")
                print(path.read_text(encoding="utf-8"))
                print()
            return 0
        for path in todo:
            conn.execute(path.read_text(encoding="utf-8"))
            conn.commit()
            print("Applied", path.name)
    return 0


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Apply Phase 1 documents migrations.")
    parser.add_argument("--database", help="Override database name (default: DB_NAME from .env)")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL only; do not execute.")
    args = parser.parse_args()
    return apply(_conninfo_from_env(args.database), dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
