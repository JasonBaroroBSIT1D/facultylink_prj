"""Read-only FacultyLink database verification report."""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

import os

EXPECTED_TABLES = sorted(
    [
        "audit_logs",
        "document_extractions",
        "documents",
        "evaluation_periods",
        "evaluation_records",
        "faculty_profiles",
        "kra_configurations",
        "kra_criteria",
        "kra_indicators",
        "kra_scores",
        "notifications",
        "rank_simulations",
        "review_decisions",
        "review_feedback",
        "reviewer_assignments",
        "scoring_rules",
        "users",
        "validation_results",
    ]
)


def main() -> int:
    conninfo = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )
    with psycopg.connect(conninfo) as conn:
        tables = [
            r[0]
            for r in conn.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY 1
                """
            )
        ]
        users = conn.execute("SELECT email, role FROM users ORDER BY 1").fetchall()
        fk = conn.execute(
            """
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE constraint_schema = 'public' AND constraint_type = 'FOREIGN KEY'
            """
        ).fetchone()[0]
        pk = conn.execute(
            """
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE constraint_schema = 'public' AND constraint_type = 'PRIMARY KEY'
            """
        ).fetchone()[0]
    print("Tables:", len(tables))
    for t in tables:
        mark = "OK" if t in EXPECTED_TABLES else "?"
        print(f"  - {t} [{mark}]")
    missing = [t for t in EXPECTED_TABLES if t not in tables]
    if missing:
        print("Missing expected tables:", ", ".join(missing))
    print("Users:", len(users))
    for email, role in users:
        print(f"  - {email} ({role})")
    print(f"Foreign keys: {fk}")
    print(f"Primary keys: {pk}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
