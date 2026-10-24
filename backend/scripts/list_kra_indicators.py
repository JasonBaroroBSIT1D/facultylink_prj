"""List kra_indicators for SET/SEF policy review (read-only)."""
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
        SELECT i.indicator_id, k.kra_code, c.criterion_code, i.indicator_code,
               i.indicator_name, i.credit_uniqueness
        FROM kra_indicators i
        JOIN kra_criteria c ON c.criterion_id = i.criterion_id
        JOIN kra_configurations k ON k.kra_id = c.kra_id
        ORDER BY k.kra_code, c.display_order, i.display_order
        """
    )
    rows = cur.fetchall()
    print(f"indicator_count: {len(rows)}")
    for row in rows:
        print(row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
