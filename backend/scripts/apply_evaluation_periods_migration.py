"""Apply 001_add_evaluation_periods.sql only when the table is missing."""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend" / "migrations" / "001_add_evaluation_periods.sql"


def main() -> int:
    load_dotenv(ROOT / ".env")
    import os

    if not MIGRATION.is_file():
        print("Migration file missing.", file=sys.stderr)
        return 1

    conninfo = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )
    with psycopg.connect(conninfo) as conn:
        exists = conn.execute("SELECT to_regclass('public.evaluation_periods') IS NOT NULL").fetchone()[0]
        if exists:
            print("evaluation_periods already exists — no migration applied.")
            return 0
        sql = MIGRATION.read_text(encoding="utf-8")
        conn.execute(sql)
        conn.commit()
        print("Applied 001_add_evaluation_periods.sql")
    return 0


if __name__ == "__main__":
    sys.exit(main())
