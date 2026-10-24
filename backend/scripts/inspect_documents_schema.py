"""Read-only inspection of documents-related schema on the configured DB."""
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
    cur.execute(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents'
        ORDER BY ordinal_position
        """
    )
    print("=== documents columns ===")
    for row in cur.fetchall():
        print(row)
    cur.execute("SELECT COUNT(*) FROM documents")
    print("documents count:", cur.fetchone()[0])
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'period_id'
        """
    )
    print("period_id on documents:", bool(cur.fetchone()))
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'document_score_contributions'
        """
    )
    print("document_score_contributions table:", bool(cur.fetchone()))
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'kra_indicators'
          AND column_name = 'credit_uniqueness'
        """
    )
    print("kra_indicators.credit_uniqueness:", bool(cur.fetchone()))
    cur.execute(
        """
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = 'document_score_contributions'
          AND indexname = 'uq_doc_score_active_credit_slot'
        """
    )
    print("uq_doc_score_active_credit_slot index:", bool(cur.fetchone()))
    cur.execute(
        """
        SELECT period_id, name, academic_year, semester, submission_enabled
        FROM evaluation_periods ORDER BY period_id LIMIT 5
        """
    )
    print("=== evaluation_periods sample ===")
    for row in cur.fetchall():
        print(row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
