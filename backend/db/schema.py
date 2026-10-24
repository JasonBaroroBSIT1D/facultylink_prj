"""Read-only schema checks against the existing PostgreSQL database."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

EXPECTED_TABLES = frozenset(
    {
        "audit_logs",
        "document_extractions",
        "document_score_contributions",
        "documents",
        "evaluation_periods",
        "evaluation_records",
        "faculty_profiles",
        "kra_configurations",
        "kra_criteria",
        "kra_criterion_operational_settings",
        "kra_indicators",
        "kra_scores",
        "notifications",
        "password_tokens",
        "password_reset_otps",
        "rank_simulations",
        "review_decisions",
        "review_feedback",
        "reviewer_assignments",
        "scoring_rules",
        "users",
        "validation_results",
    }
)


def check_database_connection(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def verify_public_schema(engine: Engine) -> tuple[bool, list[str]]:
    """Return (ok, list of issue messages). Does not modify the database."""
    issues: list[str] = []
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            )
        ).fetchall()
    tables = {row[0] for row in rows}
    missing = sorted(EXPECTED_TABLES - tables)
    extra = sorted(tables - EXPECTED_TABLES)
    if missing:
        issues.append(f"Missing tables: {', '.join(missing)}")
    if extra:
        issues.append(f"Unexpected tables: {', '.join(extra)}")
    if len(tables) != len(EXPECTED_TABLES):
        issues.append(f"Expected {len(EXPECTED_TABLES)} tables, found {len(tables)}")
    return (not issues, issues)
