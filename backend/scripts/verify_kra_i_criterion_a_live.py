"""Live verification helpers for facultylink_db (read-mostly; optional revertible metadata patch)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

API = os.getenv("FACULTYLINK_VERIFY_API", "http://127.0.0.1:5000")


def _conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def migration_005_present() -> bool:
    with psycopg.connect(_conninfo()) as conn:
        return bool(
            conn.execute(
                "SELECT to_regclass('public.kra_criterion_operational_settings') IS NOT NULL"
            ).fetchone()[0]
        )


def scoring_rules_snapshot() -> list[tuple]:
    with psycopg.connect(_conninfo()) as conn:
        return conn.execute(
            """
            SELECT sr.rule_id, i.indicator_code, sr.rule_config->>'max_points', sr.rule_name, sr.guideline_version
            FROM scoring_rules sr
            JOIN kra_indicators i ON i.indicator_id = sr.indicator_id
            JOIN kra_criteria c ON c.criterion_id = i.criterion_id
            JOIN kra_configurations k ON k.kra_id = c.kra_id
            WHERE k.kra_code = 'KRA I' AND c.criterion_code = 'A' AND sr.is_active = TRUE
            ORDER BY i.indicator_code
            """
        ).fetchall()


def main() -> int:
    print("migration_005_table_present", migration_005_present())
    print("scoring_rules_before", scoring_rules_snapshot())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
