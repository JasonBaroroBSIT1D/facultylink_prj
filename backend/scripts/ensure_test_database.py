"""Create facultylink_test_db and apply schema from development (schema-only pg_dump)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

load_dotenv(ROOT / ".env")

from testing_db_guard import FORBIDDEN_DATABASE_NAMES, database_name_from_uri  # noqa: E402


def _admin_conninfo(dbname: str = "postgres") -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={dbname} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def _target_test_db_name() -> str:
    test_url = (os.getenv("TEST_DATABASE_URL") or "").strip()
    if test_url:
        name = database_name_from_uri(test_url)
        if name:
            return name
    return "facultylink_test_db"


def _database_exists(conn: psycopg.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
    return row is not None


def _has_users_table(conn: psycopg.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users'"
    ).fetchone()
    return row is not None


def _create_database(admin: psycopg.Connection, name: str) -> None:
    admin.execute(f'CREATE DATABASE "{name}"')


def _find_pg_tool(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for pattern in (
        Path(r"C:\Program Files\PostgreSQL"),
        Path("/usr/lib/postgresql"),
    ):
        if not pattern.exists():
            continue
        for exe in pattern.rglob(f"{name}.exe" if os.name == "nt" else name):
            if exe.is_file():
                return str(exe)
    return None


def _apply_schema_from_dev(source_db: str, target_db: str) -> None:
    pg_dump = _find_pg_tool("pg_dump")
    psql = _find_pg_tool("psql")
    if not pg_dump or not psql:
        raise SystemExit(
            "pg_dump and psql must be on PATH to bootstrap the test database schema. "
            "Install PostgreSQL client tools or apply facultylink_complete_schema.sql manually."
        )
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    dump = subprocess.run(
        [
            pg_dump,
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            source_db,
            "--schema-only",
            "--no-owner",
            "--no-privileges",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if dump.returncode != 0:
        raise SystemExit(f"pg_dump failed:\n{dump.stderr}")

    load = subprocess.run(
        [psql, "-h", host, "-p", port, "-U", user, "-d", target_db, "-v", "ON_ERROR_STOP=1"],
        input=dump.stdout,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if load.returncode != 0:
        raise SystemExit(f"psql schema load failed:\n{load.stderr}")


def main() -> int:
    source_db = os.getenv("DB_NAME", "facultylink_db")
    target_db = _target_test_db_name()
    if target_db.lower() in FORBIDDEN_DATABASE_NAMES or target_db.lower() == source_db.lower():
        raise SystemExit(f"Refusing to use unsafe test database name: {target_db}")

    with psycopg.connect(_admin_conninfo("postgres")) as admin:
        admin.autocommit = True
        if not _database_exists(admin, target_db):
            print(f"Creating database {target_db!r}...")
            _create_database(admin, target_db)
        else:
            print(f"Database {target_db!r} already exists.")

    with psycopg.connect(_admin_conninfo(target_db)) as test_conn:
        if _has_users_table(test_conn):
            print(f"{target_db} already has schema (users table present). No bootstrap needed.")
            return 0

    print(f"Bootstrapping schema from {source_db!r} into {target_db!r}...")
    _apply_schema_from_dev(source_db, target_db)
    print("Test database schema ready.")
    suggested = (
        f"postgresql+psycopg://{os.getenv('DB_USER', 'postgres')}:"
        f"{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/{target_db}"
    )
    if not os.getenv("TEST_DATABASE_URL"):
        print(f"Add to .env:\nTEST_DATABASE_URL={suggested}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
