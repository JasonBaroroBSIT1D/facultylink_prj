"""Read-only prerequisite snapshot for facultylink_db verification."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main() -> int:
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "facultylink_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    cur = conn.cursor()
    cur.execute("SELECT current_database()")
    print("database:", cur.fetchone()[0])
    cur.execute("SELECT user_id, email, role, is_active FROM users ORDER BY user_id")
    print("\nusers:")
    for row in cur.fetchall():
        print(" ", row)
    cur.execute(
        "SELECT fp.faculty_id, fp.user_id, fp.employee_number, u.email "
        "FROM faculty_profiles fp JOIN users u ON u.user_id = fp.user_id"
    )
    print("\nfaculty_profiles:")
    for row in cur.fetchall():
        print(" ", row)
    cur.execute("SELECT criterion_id, criterion_code, criterion_name FROM kra_criteria LIMIT 10")
    rows = cur.fetchall()
    print(f"\nkra_criteria ({len(rows)} shown):")
    for row in rows:
        print(" ", row)
    cur.execute(
        "SELECT period_id, period_code, name, academic_year, semester FROM evaluation_periods"
    )
    print("\nevaluation_periods:")
    for row in cur.fetchall():
        print(" ", row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
