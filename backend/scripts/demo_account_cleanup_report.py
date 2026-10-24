"""Read-only report for development seed accounts (no deletes, no secrets)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DEMO_EMAILS = ("faculty@facultylink.edu", "reviewer@facultylink.edu")


def main() -> int:
    conninfo = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": os.getenv("DB_NAME", "facultylink_db"),
        "demo_accounts": [],
        "admin_preserved": "admin@facultylink.edu",
        "proposed_cleanup_steps": [],
    }

    with psycopg.connect(conninfo) as conn:
        report["connected_database"] = conn.execute("SELECT current_database()").fetchone()[0]

        for email in DEMO_EMAILS:
            row = conn.execute(
                "SELECT user_id, email, role, full_name, is_active FROM users WHERE email = %s",
                (email,),
            ).fetchone()
            if not row:
                report["demo_accounts"].append({"email": email, "found": False})
                continue

            uid, em, role, full_name, is_active = row
            entry = {
                "found": True,
                "user_id": uid,
                "email": em,
                "role": role,
                "full_name": full_name,
                "is_active": is_active,
                "dependencies": {},
            }

            if role == "faculty":
                fp = conn.execute(
                    "SELECT faculty_id, employee_number, department, college, current_rank FROM faculty_profiles WHERE user_id = %s",
                    (uid,),
                ).fetchone()
                if fp:
                    fid = fp[0]
                    entry["faculty_profile"] = {
                        "faculty_id": fid,
                        "employee_number": fp[1],
                        "department": fp[2],
                        "college": fp[3],
                        "current_rank": fp[4],
                    }
                    entry["dependencies"]["documents"] = conn.execute(
                        "SELECT COUNT(*) FROM documents WHERE faculty_id = %s", (fid,)
                    ).fetchone()[0]
                    entry["dependencies"]["reviewer_assignments_as_faculty"] = conn.execute(
                        "SELECT COUNT(*) FROM reviewer_assignments WHERE faculty_id = %s", (fid,)
                    ).fetchone()[0]
                    entry["dependencies"]["kra_scores"] = conn.execute(
                        "SELECT COUNT(*) FROM kra_scores WHERE faculty_id = %s", (fid,)
                    ).fetchone()[0]
                    entry["dependencies"]["rank_simulations"] = conn.execute(
                        "SELECT COUNT(*) FROM rank_simulations WHERE faculty_id = %s", (fid,)
                    ).fetchone()[0]

            entry["dependencies"]["reviewer_assignments_as_reviewer"] = conn.execute(
                "SELECT COUNT(*) FROM reviewer_assignments WHERE reviewer_id = %s", (uid,)
            ).fetchone()[0]
            entry["dependencies"]["review_decisions"] = conn.execute(
                "SELECT COUNT(*) FROM review_decisions WHERE reviewer_id = %s", (uid,)
            ).fetchone()[0]
            entry["dependencies"]["notifications"] = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s", (uid,)
            ).fetchone()[0]

            deps = entry["dependencies"]
            entry["safe_to_delete"] = all(v == 0 for v in deps.values())
            report["demo_accounts"].append(entry)

    report["proposed_cleanup_steps"] = [
        "1. Back up users, faculty_profiles, and dependent rows for the two demo emails.",
        "2. DELETE reviewer_assignments referencing demo faculty_id or reviewer_id (if any).",
        "3. DELETE faculty_profiles for demo faculty user_id.",
        "4. DELETE users WHERE email IN ('faculty@facultylink.edu', 'reviewer@facultylink.edu').",
        "5. Do NOT delete admin@facultylink.edu.",
        "6. Remove UI filter in productionAccounts.js after DB cleanup (optional).",
    ]

    out_dir = ROOT / "backend" / "scripts" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"demo_account_report_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nBackup report written: {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
