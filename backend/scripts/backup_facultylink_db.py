"""Create a pg_dump backup of the configured PostgreSQL database."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = ROOT / "backend" / "backups"


def _find_pg_dump() -> str | None:
    found = shutil.which("pg_dump")
    if found:
        return found
    for base in (Path(r"C:\Program Files\PostgreSQL"), Path("/usr/lib/postgresql")):
        if not base.is_dir():
            continue
        for exe in base.glob("**/pg_dump.exe" if os.name == "nt" else "**/pg_dump"):
            if exe.is_file():
                return str(exe)
    return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    pg_dump = _find_pg_dump()
    if not pg_dump:
        print("pg_dump not found. Install PostgreSQL client tools.", file=sys.stderr)
        return 1

    db_name = os.getenv("DB_NAME", "facultylink_db")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = BACKUP_DIR / f"{db_name}_{stamp}.sql"

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        pg_dump,
        "-h",
        host,
        "-p",
        str(port),
        "-U",
        user,
        "-d",
        db_name,
        "--no-owner",
        "--no-privileges",
        "-f",
        str(out_path),
    ]
    print("Running:", " ".join(cmd[:8]), "...", str(out_path))
    subprocess.run(cmd, env=env, check=True)

    size = out_path.stat().st_size
    if size < 100:
        print("Backup file suspiciously small.", file=sys.stderr)
        return 1
    print(f"Backup OK: {out_path} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
