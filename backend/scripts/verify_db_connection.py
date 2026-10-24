"""Print current_database() for configured DB_NAME."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main() -> int:
    db_name = os.getenv("DB_NAME", "facultylink_db")
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=db_name,
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    cur = conn.cursor()
    cur.execute("SELECT current_database()")
    current = cur.fetchone()[0]
    print(f"DB_NAME env: {db_name}")
    print(f"current_database(): {current}")
    conn.close()
    return 0 if current == db_name else 1


if __name__ == "__main__":
    sys.exit(main())
