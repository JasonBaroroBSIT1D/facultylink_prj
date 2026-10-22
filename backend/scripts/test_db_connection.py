"""Quick PostgreSQL connectivity check using backend.config (loads .env)."""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Config  # noqa: E402


def main() -> int:
    try:
        with psycopg.connect(Config.psycopg_conninfo()) as conn:
            version = conn.execute("SELECT version()").fetchone()[0]
            tables = conn.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            ).fetchone()[0]
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        print("Connection OK")
        print(f"PostgreSQL: {version.split(',')[0]}")
        print(f"Public tables: {tables}")
        print(f"Users: {users}")
        return 0
    except Exception as exc:
        print(f"Connection failed: {exc.__class__.__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
