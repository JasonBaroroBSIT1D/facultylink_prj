"""Delete a fixed set of users from development PostgreSQL (dry-run by default).

No TRUNCATE, DROP TABLE, or CASCADE. Uses a single transaction on --execute.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# User-approved ID list — each ID must match EXPECTED_EMAIL at runtime.
TARGET_USERS: tuple[tuple[int, str], ...] = (
    (111, "fchg-822937@facultylink.test"),
    (112, "otp-0c87be@facultylink.test"),
    (115, "reviewer@facultylink.edu"),
    (116, "faculty@facultylink.edu"),
    (124, "otp-2657a6@facultylink.test"),
    (127, "reviewer2-c99abe@facultylink.test"),
    (145, "jasonbaroro4@gmail.com"),
    (146, "jasonbaroro5@gmail.com"),
)

TARGET_IDS = frozenset(uid for uid, _ in TARGET_USERS)

# Canonical demo seed accounts — deleting them removes default demo login pair.
DEMO_SEED_IDS = frozenset({115, 116})

ADMIN_ROLE = "admin"


def _conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def _fetch_user(conn: psycopg.Connection, user_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT user_id, email, role, full_name, is_active FROM users WHERE user_id = %s",
        (user_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "user_id": row[0],
        "email": row[1],
        "role": row[2],
        "full_name": row[3],
        "is_active": row[4],
    }


def _faculty_ids(conn: psycopg.Connection, user_ids: list[int]) -> list[int]:
    rows = conn.execute(
        "SELECT faculty_id FROM faculty_profiles WHERE user_id = ANY(%s)",
        (user_ids,),
    ).fetchall()
    return [r[0] for r in rows]


def _document_ids(conn: psycopg.Connection, faculty_ids: list[int]) -> list[int]:
    if not faculty_ids:
        return []
    rows = conn.execute(
        "SELECT document_id FROM documents WHERE faculty_id = ANY(%s)",
        (faculty_ids,),
    ).fetchall()
    return [r[0] for r in rows]


def _count(conn: psycopg.Connection, sql: str, params: tuple) -> int:
    return conn.execute(sql, params).fetchone()[0]


def validate_targets(conn: psycopg.Connection) -> list[str]:
    errors: list[str] = []
    for user_id, expected_email in TARGET_USERS:
        user = _fetch_user(conn, user_id)
        if not user:
            errors.append(f"user_id {user_id} not found")
            continue
        if user["role"] == ADMIN_ROLE:
            errors.append(f"user_id {user_id} is an administrator — refused")
        if (user["email"] or "").lower() != expected_email.lower():
            errors.append(
                f"user_id {user_id} email mismatch: db={user['email']!r} expected={expected_email!r}"
            )
    admins = conn.execute(
        "SELECT user_id FROM users WHERE role = %s AND user_id = ANY(%s)",
        (ADMIN_ROLE, list(TARGET_IDS)),
    ).fetchall()
    if admins:
        errors.append(f"Target list includes admin user_id(s): {[r[0] for r in admins]}")
    return errors


def preview_counts(conn: psycopg.Connection) -> dict[str, int]:
    uid_list = list(TARGET_IDS)
    faculty_ids = _faculty_ids(conn, uid_list)
    doc_ids = _document_ids(conn, faculty_ids)
    counts: dict[str, int] = {}

    counts["users"] = len(TARGET_USERS)
    counts["faculty_profiles"] = _count(
        conn, "SELECT COUNT(*) FROM faculty_profiles WHERE user_id = ANY(%s)", (uid_list,)
    )
    counts["password_reset_otps"] = _count(
        conn, "SELECT COUNT(*) FROM password_reset_otps WHERE user_id = ANY(%s)", (uid_list,)
    )
    counts["password_tokens"] = _count(
        conn, "SELECT COUNT(*) FROM password_tokens WHERE user_id = ANY(%s)", (uid_list,)
    )
    counts["notifications"] = _count(
        conn, "SELECT COUNT(*) FROM notifications WHERE user_id = ANY(%s)", (uid_list,)
    )
    counts["audit_logs (user_id, will SET NULL)"] = _count(
        conn, "SELECT COUNT(*) FROM audit_logs WHERE user_id = ANY(%s)", (uid_list,)
    )
    counts["reviewer_assignments (reviewer_id)"] = _count(
        conn, "SELECT COUNT(*) FROM reviewer_assignments WHERE reviewer_id = ANY(%s)", (uid_list,)
    )
    counts["reviewer_assignments (faculty_id)"] = _count(
        conn,
        "SELECT COUNT(*) FROM reviewer_assignments WHERE faculty_id = ANY(%s)",
        (faculty_ids if faculty_ids else [-1],),
    )
    counts["review_decisions (reviewer_id)"] = _count(
        conn, "SELECT COUNT(*) FROM review_decisions WHERE reviewer_id = ANY(%s)", (uid_list,)
    )
    counts["review_feedback (reviewer_id)"] = _count(
        conn, "SELECT COUNT(*) FROM review_feedback WHERE reviewer_id = ANY(%s)", (uid_list,)
    )
    counts["documents"] = len(doc_ids)
    if doc_ids:
        counts["document_extractions"] = _count(
            conn, "SELECT COUNT(*) FROM document_extractions WHERE document_id = ANY(%s)", (doc_ids,)
        )
        counts["validation_results"] = _count(
            conn, "SELECT COUNT(*) FROM validation_results WHERE document_id = ANY(%s)", (doc_ids,)
        )
        counts["evaluation_records (via documents)"] = _count(
            conn, "SELECT COUNT(*) FROM evaluation_records WHERE document_id = ANY(%s)", (doc_ids,)
        )
        counts["review_decisions (via documents)"] = _count(
            conn, "SELECT COUNT(*) FROM review_decisions WHERE document_id = ANY(%s)", (doc_ids,)
        )
        counts["review_feedback (via documents)"] = _count(
            conn, "SELECT COUNT(*) FROM review_feedback WHERE document_id = ANY(%s)", (doc_ids,)
        )
    else:
        for k in (
            "document_extractions",
            "validation_results",
            "evaluation_records (via documents)",
            "review_decisions (via documents)",
            "review_feedback (via documents)",
        ):
            counts[k] = 0
    if faculty_ids:
        counts["evaluation_records (faculty_id)"] = _count(
            conn, "SELECT COUNT(*) FROM evaluation_records WHERE faculty_id = ANY(%s)", (faculty_ids,)
        )
        counts["kra_scores"] = _count(
            conn, "SELECT COUNT(*) FROM kra_scores WHERE faculty_id = ANY(%s)", (faculty_ids,)
        )
        counts["rank_simulations"] = _count(
            conn, "SELECT COUNT(*) FROM rank_simulations WHERE faculty_id = ANY(%s)", (faculty_ids,)
        )
    else:
        counts["evaluation_records (faculty_id)"] = 0
        counts["kra_scores"] = 0
        counts["rank_simulations"] = 0
    return counts


def emit_sql(conn: psycopg.Connection) -> str:
    uid_list = list(TARGET_IDS)
    faculty_ids = _faculty_ids(conn, uid_list)
    doc_ids = _document_ids(conn, faculty_ids)
    lines = [
        "-- FacultyLink user batch cleanup (generated)",
        "-- Review dry-run output before executing.",
        "BEGIN;",
        "",
    ]
    if doc_ids:
        lines.append(f"-- document_ids: {doc_ids}")
        lines.append(
            "DELETE FROM review_feedback WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append(
            "DELETE FROM review_decisions WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append(
            "DELETE FROM evaluation_records WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append(
            "DELETE FROM validation_results WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append(
            "DELETE FROM document_extractions WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append(
            "DELETE FROM documents WHERE document_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in doc_ids)
        )
        lines.append("")
    if faculty_ids:
        lines.append(f"-- faculty_ids: {faculty_ids}")
        lines.append(
            "DELETE FROM evaluation_records WHERE faculty_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in faculty_ids)
        )
        lines.append(
            "DELETE FROM kra_scores WHERE faculty_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in faculty_ids)
        )
        lines.append(
            "DELETE FROM rank_simulations WHERE faculty_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in faculty_ids)
        )
        lines.append(
            "DELETE FROM reviewer_assignments WHERE faculty_id = ANY(ARRAY[%s]::bigint[]);"
            % ",".join(str(i) for i in faculty_ids)
        )
        lines.append("")
    lines.append(
        "DELETE FROM reviewer_assignments WHERE reviewer_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM review_feedback WHERE reviewer_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM review_decisions WHERE reviewer_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM password_reset_otps WHERE user_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM password_tokens WHERE user_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM notifications WHERE user_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "UPDATE audit_logs SET user_id = NULL WHERE user_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    lines.append(
        "DELETE FROM faculty_profiles WHERE user_id = ANY(ARRAY[%s]::bigint[]);"
        % ",".join(str(i) for i in uid_list)
    )
    for uid, email in TARGET_USERS:
        esc = email.replace("'", "''")
        lines.append(
            f"DELETE FROM users WHERE user_id = {uid} AND lower(email) = lower('{esc}');"
        )
    lines.extend(["", "-- COMMIT;  -- uncomment after manual review", "ROLLBACK;"])
    return "\n".join(lines)


def execute_deletes(conn: psycopg.Connection) -> None:
    uid_list = list(TARGET_IDS)
    faculty_ids = _faculty_ids(conn, uid_list)
    doc_ids = _document_ids(conn, faculty_ids)

    with conn.transaction():
        if doc_ids:
            conn.execute("DELETE FROM review_feedback WHERE document_id = ANY(%s)", (doc_ids,))
            conn.execute("DELETE FROM review_decisions WHERE document_id = ANY(%s)", (doc_ids,))
            conn.execute("DELETE FROM evaluation_records WHERE document_id = ANY(%s)", (doc_ids,))
            conn.execute("DELETE FROM validation_results WHERE document_id = ANY(%s)", (doc_ids,))
            conn.execute("DELETE FROM document_extractions WHERE document_id = ANY(%s)", (doc_ids,))
            conn.execute("DELETE FROM documents WHERE document_id = ANY(%s)", (doc_ids,))
        if faculty_ids:
            conn.execute("DELETE FROM evaluation_records WHERE faculty_id = ANY(%s)", (faculty_ids,))
            conn.execute("DELETE FROM kra_scores WHERE faculty_id = ANY(%s)", (faculty_ids,))
            conn.execute("DELETE FROM rank_simulations WHERE faculty_id = ANY(%s)", (faculty_ids,))
            conn.execute("DELETE FROM reviewer_assignments WHERE faculty_id = ANY(%s)", (faculty_ids,))
        conn.execute("DELETE FROM reviewer_assignments WHERE reviewer_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM review_feedback WHERE reviewer_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM review_decisions WHERE reviewer_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM password_reset_otps WHERE user_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM password_tokens WHERE user_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM notifications WHERE user_id = ANY(%s)", (uid_list,))
        conn.execute("UPDATE audit_logs SET user_id = NULL WHERE user_id = ANY(%s)", (uid_list,))
        conn.execute("DELETE FROM faculty_profiles WHERE user_id = ANY(%s)", (uid_list,))
        for user_id, expected_email in TARGET_USERS:
            deleted = conn.execute(
                "DELETE FROM users WHERE user_id = %s AND lower(email) = lower(%s)",
                (user_id, expected_email),
            ).rowcount
            if deleted != 1:
                raise RuntimeError(f"users delete affected {deleted} rows for user_id={user_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch user cleanup with dry-run preview.")
    parser.add_argument("--execute", action="store_true", help="Run deletion in a transaction.")
    parser.add_argument(
        "--confirm",
        default="",
        help='Required with --execute: type exactly "DELETE USERS BATCH" to proceed.',
    )
    parser.add_argument(
        "--acknowledge-demo-seed-deletion",
        action="store_true",
        help=f"Required when targets include demo seed IDs {sorted(DEMO_SEED_IDS)}.",
    )
    parser.add_argument("--emit-sql", action="store_true", help="Print PostgreSQL script and exit.")
    args = parser.parse_args()

    with psycopg.connect(_conninfo()) as conn:
        db = conn.execute("SELECT current_database()").fetchone()[0]
        print(f"Connected to: {db}\n")

        admins = conn.execute(
            "SELECT user_id, email, full_name FROM users WHERE role = %s ORDER BY user_id",
            (ADMIN_ROLE,),
        ).fetchall()
        print("Preserved administrator(s) (not in delete list):")
        for a in admins:
            print(f"  user_id={a[0]} email={a[1]} name={a[2]}")
        if not admins:
            print("  WARNING: No admin user found.")
        print()

        errors = validate_targets(conn)
        if errors:
            print("VALIDATION FAILED — stopping:")
            for e in errors:
                print(f"  - {e}")
            return 1

        print("Target users (ID + email verified):")
        for uid, email in TARGET_USERS:
            u = _fetch_user(conn, uid)
            print(f"  {uid}: {u['email']} ({u['role']}) — {u['full_name']}")
        print()

        demo_hit = TARGET_IDS & DEMO_SEED_IDS
        if demo_hit:
            print("⚠ UNEXPECTED / HIGH-IMPACT IDENTITIES:")
            print(
                "  user_id 115 (reviewer@facultylink.edu) and 116 (faculty@facultylink.edu) "
                "are the standard demo seed accounts used for local testing and demos."
            )
            print(
                "  user_id 145/146 are real reviewer accounts (Jason/Jenny Baroro), not pytest leftovers."
            )
            print("  After deletion, only admin remains until you create new accounts or run:")
            print("    python backend/scripts/ensure_demo_dev_accounts.py")
            print()
            if not args.acknowledge_demo_seed_deletion and not args.emit_sql:
                print(
                    "STOP: Re-run with --acknowledge-demo-seed-deletion to confirm you intend to "
                    "delete demo seed accounts 115 and 116."
                )
                if args.execute:
                    return 1

        faculty_ids = _faculty_ids(conn, list(TARGET_IDS))
        if faculty_ids:
            rows = conn.execute(
                "SELECT assignment_id, reviewer_id, faculty_id, assigned_by FROM reviewer_assignments "
                "WHERE faculty_id = ANY(%s) OR reviewer_id = ANY(%s) ORDER BY assignment_id",
                (faculty_ids, list(TARGET_IDS)),
            ).fetchall()
            if rows:
                print("Reviewer assignments that will be removed:")
                for r in rows:
                    print(f"  assignment_id={r[0]} reviewer_id={r[1]} faculty_id={r[2]} assigned_by={r[3]}")
                print()

        counts = preview_counts(conn)
        print("Dry-run affected record counts:")
        for key in sorted(counts.keys()):
            print(f"  {key}: {counts[key]}")
        print()

        remaining = conn.execute("SELECT COUNT(*) FROM users WHERE user_id NOT IN (SELECT unnest(%s::bigint[]))", (list(TARGET_IDS),)).fetchone()[0]
        print(f"Users remaining after delete (expected ≥1 admin): {remaining}")
        print()

        if args.emit_sql:
            print(emit_sql(conn))
            return 0

        if not args.execute:
            print('DRY RUN ONLY — no changes made.')
            print('Next: review counts, then --emit-sql or --execute --confirm "DELETE USERS BATCH" '
                  '--acknowledge-demo-seed-deletion')
            return 0

        if args.confirm != "DELETE USERS BATCH":
            print('Refusing --execute without --confirm "DELETE USERS BATCH"')
            return 1
        if demo_hit and not args.acknowledge_demo_seed_deletion:
            print("Refusing --execute without --acknowledge-demo-seed-deletion")
            return 1

        try:
            execute_deletes(conn)
        except Exception as exc:
            print(f"Deletion failed (transaction rolled back): {exc}")
            return 1
        print("Deletion completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
