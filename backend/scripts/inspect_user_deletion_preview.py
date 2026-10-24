"""Read-only dependency preview for proposed user deletions (development DB)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

TARGET_USER_IDS = (111, 112, 115, 116, 124, 127, 145, 146)

# Emails recorded from prior verification / pytest artifacts — mismatch aborts preview.
EXPECTED_EMAIL_BY_ID: dict[int, str] = {
    111: "",  # filled from DB snapshot during script run if empty — user must confirm
    112: "otp-0c87be@facultylink.test",
    115: "",
    116: "",
    124: "otp-2657a6@facultylink.test",
    127: "reviewer2-c99abe@facultylink.test",
    145: "jasonbaroro4@gmail.com",
    146: "",
}


def _conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def main() -> int:
    with psycopg.connect(_conninfo()) as conn:
        db = conn.execute("SELECT current_database()").fetchone()[0]
        print(f"Database: {db}\n")

        admins = conn.execute(
            "SELECT user_id, email, full_name FROM users WHERE role = 'admin' ORDER BY user_id"
        ).fetchall()
        print("System administrator account(s):")
        for row in admins:
            print(f"  user_id={row[0]} email={row[1]} name={row[2]}")
        admin_ids = {r[0] for r in admins}
        overlap = admin_ids & set(TARGET_USER_IDS)
        if overlap:
            print(f"\nABORT: Target list includes admin user_id(s): {sorted(overlap)}")
            return 1

        users: list[dict] = []
        for uid in TARGET_USER_IDS:
            row = conn.execute(
                "SELECT user_id, email, role, full_name, is_active FROM users WHERE user_id = %s",
                (uid,),
            ).fetchone()
            if not row:
                print(f"ABORT: user_id {uid} not found.")
                return 1
            users.append(
                {
                    "user_id": row[0],
                    "email": row[1],
                    "role": row[2],
                    "full_name": row[3],
                    "is_active": row[4],
                }
            )

        print("\nTarget users (database):")
        mismatches: list[str] = []
        for u in users:
            exp = EXPECTED_EMAIL_BY_ID.get(u["user_id"], "")
            line = f"  {u['user_id']}: {u['email']} ({u['role']}) — {u['full_name']}"
            if exp and exp.lower() != (u["email"] or "").lower():
                mismatches.append(f"user_id {u['user_id']}: db={u['email']!r} expected={exp!r}")
            print(line)
        if mismatches:
            print("\nEMAIL MISMATCH (update EXPECTED_EMAIL_BY_ID or target list):")
            for m in mismatches:
                print(f"  - {m}")
            return 1

        faculty_ids: list[int] = []
        for u in users:
            fp = conn.execute(
                "SELECT faculty_id, employee_number FROM faculty_profiles WHERE user_id = %s",
                (u["user_id"],),
            ).fetchone()
            u["faculty_id"] = fp[0] if fp else None
            u["employee_number"] = fp[1] if fp else None
            if fp:
                faculty_ids.append(fp[0])

        counts: dict[str, int | list] = {}

        def cnt(sql: str, params: tuple) -> int:
            return conn.execute(sql, params).fetchone()[0]

        uid_list = tuple(TARGET_USER_IDS)
        fid_list = tuple(faculty_ids) if faculty_ids else (-1,)

        # Direct user FKs
        counts["password_reset_otps"] = cnt(
            "SELECT COUNT(*) FROM password_reset_otps WHERE user_id = ANY(%s)", (list(uid_list),)
        )
        counts["password_tokens"] = cnt(
            "SELECT COUNT(*) FROM password_tokens WHERE user_id = ANY(%s)", (list(uid_list),)
        )
        counts["notifications"] = cnt(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ANY(%s)", (list(uid_list),)
        )
        counts["audit_logs (user_id)"] = cnt(
            "SELECT COUNT(*) FROM audit_logs WHERE user_id = ANY(%s)", (list(uid_list),)
        )
        counts["reviewer_assignments (reviewer_id)"] = cnt(
            "SELECT COUNT(*) FROM reviewer_assignments WHERE reviewer_id = ANY(%s)", (list(uid_list),)
        )
        counts["reviewer_assignments (assigned_by)"] = cnt(
            "SELECT COUNT(*) FROM reviewer_assignments WHERE assigned_by = ANY(%s)", (list(uid_list),)
        )
        counts["review_decisions (reviewer_id)"] = cnt(
            "SELECT COUNT(*) FROM review_decisions WHERE reviewer_id = ANY(%s)", (list(uid_list),)
        )
        counts["review_feedback (reviewer_id)"] = cnt(
            "SELECT COUNT(*) FROM review_feedback WHERE reviewer_id = ANY(%s)", (list(uid_list),)
        )
        counts["faculty_profiles"] = cnt(
            "SELECT COUNT(*) FROM faculty_profiles WHERE user_id = ANY(%s)", (list(uid_list),)
        )

        # Faculty-scoped chains
        if faculty_ids:
            doc_ids = [
                r[0]
                for r in conn.execute(
                    "SELECT document_id FROM documents WHERE faculty_id = ANY(%s)",
                    (faculty_ids,),
                ).fetchall()
            ]
            counts["documents"] = len(doc_ids)
            if doc_ids:
                counts["document_extractions"] = cnt(
                    "SELECT COUNT(*) FROM document_extractions WHERE document_id = ANY(%s)",
                    (doc_ids,),
                )
                counts["validation_results"] = cnt(
                    "SELECT COUNT(*) FROM validation_results WHERE document_id = ANY(%s)",
                    (doc_ids,),
                )
                counts["evaluation_records"] = cnt(
                    "SELECT COUNT(*) FROM evaluation_records WHERE document_id = ANY(%s)",
                    (doc_ids,),
                )
                counts["review_decisions (on faculty docs)"] = cnt(
                    "SELECT COUNT(*) FROM review_decisions WHERE document_id = ANY(%s)",
                    (doc_ids,),
                )
                counts["review_feedback (on faculty docs)"] = cnt(
                    "SELECT COUNT(*) FROM review_feedback WHERE document_id = ANY(%s)",
                    (doc_ids,),
                )
            else:
                for k in (
                    "document_extractions",
                    "validation_results",
                    "evaluation_records",
                    "review_decisions (on faculty docs)",
                    "review_feedback (on faculty docs)",
                ):
                    counts[k] = 0
            counts["evaluation_records (by faculty_id)"] = cnt(
                "SELECT COUNT(*) FROM evaluation_records WHERE faculty_id = ANY(%s)",
                (faculty_ids,),
            )
            counts["kra_scores"] = cnt(
                "SELECT COUNT(*) FROM kra_scores WHERE faculty_id = ANY(%s)",
                (faculty_ids,),
            )
            counts["rank_simulations"] = cnt(
                "SELECT COUNT(*) FROM rank_simulations WHERE faculty_id = ANY(%s)",
                (faculty_ids,),
            )
            counts["reviewer_assignments (faculty_id)"] = cnt(
                "SELECT COUNT(*) FROM reviewer_assignments WHERE faculty_id = ANY(%s)",
                (faculty_ids,),
            )
        else:
            for k in (
                "documents",
                "document_extractions",
                "validation_results",
                "evaluation_records",
                "review_decisions (on faculty docs)",
                "review_feedback (on faculty docs)",
                "evaluation_records (by faculty_id)",
                "kra_scores",
                "rank_simulations",
                "reviewer_assignments (faculty_id)",
            ):
                counts[k] = 0

        counts["audit_logs (entity user)"] = cnt(
            """
            SELECT COUNT(*) FROM audit_logs
            WHERE entity_type = 'user' AND entity_id = ANY(%s)
            """,
            ([str(i) for i in uid_list],),
        )

        # assigned_by on OTHER users' rows pointing to targets — only NULL or reassign needed?
        # Deleting users who are assigned_by: FK may block — check ON DELETE
        assigned_by_refs = conn.execute(
            """
            SELECT assignment_id, reviewer_id, faculty_id, assigned_by
            FROM reviewer_assignments WHERE assigned_by = ANY(%s)
            """,
            (list(uid_list),),
        ).fetchall()

        print("\nPer-user faculty_id:")
        for u in users:
            print(f"  {u['user_id']}: faculty_id={u.get('faculty_id')}")

        print("\nDry-run affected record counts:")
        for key in sorted(counts.keys()):
            print(f"  {key}: {counts[key]}")

        if assigned_by_refs:
            print("\nReviewer assignments where target user is assigned_by (must NULL or delete assignment first):")
            for row in assigned_by_refs:
                print(f"  assignment_id={row[0]} reviewer_id={row[1]} faculty_id={row[2]} assigned_by={row[3]}")

        # Check FK constraints on users
        print("\nTarget users rows:", len(users))
        print(json.dumps({"users": users, "counts": counts}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
