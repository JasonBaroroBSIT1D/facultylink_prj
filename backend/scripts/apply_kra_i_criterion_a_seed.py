"""Apply KRA I Criterion A seed to DB_NAME from .env (facultylink_db only when configured)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "backend" / "scripts" / "kra_i_criterion_a_jc01_2026.sql.example"


def main() -> int:
    load_dotenv(ROOT / ".env")
    db_name = os.getenv("DB_NAME", "")
    if db_name != "facultylink_db":
        print(f"Refusing: DB_NAME is {db_name!r}, expected facultylink_db.", file=sys.stderr)
        return 1
    if not SEED.is_file():
        print("Seed file missing.", file=sys.stderr)
        return 1
    sql = SEED.read_text(encoding="utf-8")
    if "DELETE" in sql.upper() or "TRUNCATE" in sql.upper() or "DROP TABLE" in sql.upper():
        print("Seed contains destructive statements.", file=sys.stderr)
        return 1
    if sql.strip().endswith("ROLLBACK;"):
        sql = sql.rsplit("ROLLBACK;", 1)[0] + "COMMIT;"
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=db_name,
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    with conn:
        conn.execute("SELECT current_database()").fetchone()
        cur = conn.execute(
            "SELECT COUNT(*) FROM kra_configurations WHERE kra_code NOT IN ('KRA I')"
        )
        other_kra = cur.fetchone()[0]
        if other_kra:
            print(f"Unexpected: {other_kra} non-KRA-I configuration rows exist.", file=sys.stderr)
            return 1
        conn.execute(sql)
    print("Applied KRA I Criterion A seed with COMMIT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
