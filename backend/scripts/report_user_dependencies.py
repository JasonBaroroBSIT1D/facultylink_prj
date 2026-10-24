"""Read-only demo user dependency report (no secrets printed)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main() -> int:
    conninfo = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )
    with psycopg.connect(conninfo) as conn:
        db = conn.execute("SELECT current_database()").fetchone()[0]
        user = conn.execute("SELECT current_user").fetchone()[0]
        print(f"Connected database: {db}")
        print(f"Connected role: {user}")
        rows = conn.execute(
            "SELECT user_id, email, role, is_active FROM users ORDER BY user_id"
        ).fetchall()
        for uid, email, role, active in rows:
            print(f"\nuser_id={uid} email={email} role={role} active={active}")
            fp = conn.execute(
                "SELECT faculty_id FROM faculty_profiles WHERE user_id = %s", (uid,)
            ).fetchone()
            if fp:
                fid = fp[0]
                docs = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE faculty_id = %s", (fid,)
                ).fetchone()[0]
                print(f"  faculty_id={fid} documents={docs}")
            ra_rev = conn.execute(
                "SELECT COUNT(*) FROM reviewer_assignments WHERE reviewer_id = %s",
                (uid,),
            ).fetchone()[0]
            ra_by = conn.execute(
                "SELECT COUNT(*) FROM reviewer_assignments WHERE assigned_by = %s",
                (uid,),
            ).fetchone()[0]
            rd = conn.execute(
                "SELECT COUNT(*) FROM review_decisions WHERE reviewer_id = %s", (uid,)
            ).fetchone()[0]
            audit = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE entity_type = 'user' AND entity_id = %s",
                (str(uid),),
            ).fetchone()[0]
            print(f"  reviewer_assignments(reviewer)={ra_rev} assigned_by={ra_by}")
            print(f"  review_decisions={rd} audit_logs(user)={audit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
