"""
Initialize facultylink_db from facultylink_complete_schema.sql (empty DB only).
Reads credentials from project-root .env — never log passwords.
"""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "facultylink_complete_schema.sql"

EXPECTED_TABLES = frozenset(
    {
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
    }
)

EXPECTED_FK_COUNT_MIN = 25
EXPECTED_USER_EMAILS = frozenset(
    {
        "admin@facultylink.edu",
        "reviewer@facultylink.edu",
        "faculty@facultylink.edu",
    }
)


def load_config():
    load_dotenv(ROOT / ".env")
    import os

    cfg = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "dbname": os.getenv("DB_NAME", "facultylink_db"),
    }
    if not cfg["password"]:
        print("ERROR: DB_PASSWORD is not set. Copy .env.example to .env and configure it.", file=sys.stderr)
        sys.exit(1)
    return cfg


def main() -> int:
    if not SCHEMA.is_file():
        print(f"ERROR: Schema file not found: {SCHEMA}", file=sys.stderr)
        return 1

    sql_text = SCHEMA.read_text(encoding="utf-8")
    if "CREATE TABLE evaluation_periods" not in sql_text:
        print("ERROR: Schema incomplete — evaluation_periods table missing.", file=sys.stderr)
        return 1
    if sql_text.count("CREATE TABLE") != 18:
        print(f"ERROR: Expected 18 CREATE TABLE statements, found {sql_text.count('CREATE TABLE')}.", file=sys.stderr)
        return 1

    cfg = load_config()
    admin_db = "postgres"

    try:
        with psycopg.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname=admin_db,
            autocommit=True,
        ) as admin_conn:
            exists = admin_conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (cfg["dbname"],)
            ).fetchone()
            if not exists:
                admin_conn.execute(
                    psycopg.sql.SQL("CREATE DATABASE {}").format(
                        psycopg.sql.Identifier(cfg["dbname"])
                    )
                )
                print(f"Created database: {cfg['dbname']}")
            else:
                print(f"Database already exists: {cfg['dbname']}")

        with psycopg.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname=cfg["dbname"],
        ) as conn:
            table_count = conn.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            ).fetchone()[0]

            if table_count > 0:
                print(
                    f"STOP: Database '{cfg['dbname']}' is not empty ({table_count} public tables). "
                    "No schema was applied. Use migration tooling if you need to upgrade.",
                    file=sys.stderr,
                )
                return 2

            print("Applying facultylink_complete_schema.sql (single transaction)...")
            conn.execute(sql_text)
            conn.commit()
            print("Schema applied successfully.")

            tables = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
            }
            if tables != EXPECTED_TABLES:
                missing = EXPECTED_TABLES - tables
                extra = tables - EXPECTED_TABLES
                print(f"ERROR: Table set mismatch. Missing: {sorted(missing)} Extra: {sorted(extra)}", file=sys.stderr)
                return 1
            print(f"Verified {len(tables)} public tables.")

            users = conn.execute("SELECT email, role FROM users ORDER BY email").fetchall()
            emails = {u[0] for u in users}
            if emails != EXPECTED_USER_EMAILS or len(users) != 3:
                print(f"ERROR: Expected 3 demo users, found: {users}", file=sys.stderr)
                return 1
            print("Verified 3 development accounts (admin, reviewer, faculty).")

            fk_count = conn.execute(
                """
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema = 'public' AND constraint_type = 'FOREIGN KEY'
                """
            ).fetchone()[0]
            if fk_count < EXPECTED_FK_COUNT_MIN:
                print(f"ERROR: Expected at least {EXPECTED_FK_COUNT_MIN} foreign keys, found {fk_count}.", file=sys.stderr)
                return 1
            print(f"Verified {fk_count} foreign key constraints.")

            period = conn.execute(
                "SELECT to_regclass('public.evaluation_periods') IS NOT NULL"
            ).fetchone()[0]
            if not period:
                print("ERROR: evaluation_periods table not found.", file=sys.stderr)
                return 1
            print("Verified evaluation_periods table.")

            pk_count = conn.execute(
                """
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema = 'public' AND constraint_type = 'PRIMARY KEY'
                """
            ).fetchone()[0]
            print(f"Verified {pk_count} primary key constraints.")

    except psycopg.Error as exc:
        print(f"ERROR: PostgreSQL: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    print("Database setup complete. facultylink_db is ready for Flask connection tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
