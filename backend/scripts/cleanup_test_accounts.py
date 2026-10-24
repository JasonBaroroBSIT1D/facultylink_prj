"""One-time cleanup of verified pytest leftovers on the development database (dry-run by default)."""
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

# Verified targets only — re-checked before any delete.
TARGET_USERS: tuple[tuple[int, str], ...] = (
    (112, "otp-0c87be@facultylink.test"),
    (124, "otp-2657a6@facultylink.test"),
    (127, "reviewer2-c99abe@facultylink.test"),
)

PRESERVE_USER_IDS = frozenset({145})  # Jason Baroro
PRESERVE_ASSIGNMENT_IDS = frozenset({11})
EXPECTED_ASSIGNMENT_FOR_127 = (8, 127)  # assignment_id, reviewer_id


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


def _dependency_rows(conn: psycopg.Connection, user_id: int) -> dict[str, list[tuple]]:
    out: dict[str, list[tuple]] = {}
    out["password_reset_otps"] = conn.execute(
        "SELECT otp_id, user_id, expires_at FROM password_reset_otps WHERE user_id = %s ORDER BY otp_id",
        (user_id,),
    ).fetchall()
    out["password_tokens"] = conn.execute(
        "SELECT token_id, user_id, purpose, expires_at FROM password_tokens WHERE user_id = %s ORDER BY token_id",
        (user_id,),
    ).fetchall()
    out["faculty_profiles"] = conn.execute(
        "SELECT faculty_id, user_id FROM faculty_profiles WHERE user_id = %s",
        (user_id,),
    ).fetchall()
    out["reviewer_assignments_as_reviewer"] = conn.execute(
        "SELECT assignment_id, reviewer_id, faculty_id, assigned_by FROM reviewer_assignments "
        "WHERE reviewer_id = %s ORDER BY assignment_id",
        (user_id,),
    ).fetchall()
    out["reviewer_assignments_as_assigner"] = conn.execute(
        "SELECT assignment_id, reviewer_id, faculty_id FROM reviewer_assignments WHERE assigned_by = %s",
        (user_id,),
    ).fetchall()
    out["review_decisions"] = conn.execute(
        "SELECT decision_id, reviewer_id FROM review_decisions WHERE reviewer_id = %s",
        (user_id,),
    ).fetchall()
    return out


def _validate_targets(conn: psycopg.Connection) -> list[str]:
    errors: list[str] = []
    for user_id, expected_email in TARGET_USERS:
        if user_id in PRESERVE_USER_IDS:
            errors.append(f"Refusing to target preserved user_id {user_id}")
            continue
        user = _fetch_user(conn, user_id)
        if not user:
            errors.append(f"user_id {user_id} not found (expected {expected_email})")
            continue
        if (user["email"] or "").lower() != expected_email.lower():
            errors.append(
                f"user_id {user_id} email mismatch: db={user['email']!r} expected={expected_email!r}"
            )
    aid, rid = EXPECTED_ASSIGNMENT_FOR_127
    row = conn.execute(
        "SELECT assignment_id, reviewer_id, faculty_id FROM reviewer_assignments WHERE assignment_id = %s",
        (aid,),
    ).fetchone()
    if not row:
        errors.append(f"Expected reviewer assignment {aid} missing")
    elif row[1] != rid:
        errors.append(f"Assignment {aid} reviewer_id={row[1]} expected {rid}")

    for preserve_id in PRESERVE_ASSIGNMENT_IDS:
        prow = conn.execute(
            "SELECT assignment_id, reviewer_id, faculty_id FROM reviewer_assignments WHERE assignment_id = %s",
            (preserve_id,),
        ).fetchone()
        if not prow:
            errors.append(f"Preserved assignment {preserve_id} is missing — abort.")
    jason = _fetch_user(conn, 145)
    if not jason or "jasonbaroro" not in (jason["email"] or "").lower():
        errors.append("Preserve check failed for user_id 145 (Jason Baroro)")
    return errors


def _planned_deletes(conn: psycopg.Connection) -> list[tuple[str, str, tuple]]:
    """Return (table, description, params) delete operations in FK-safe order."""
    ops: list[tuple[str, str, tuple]] = []
    for user_id, expected_email in TARGET_USERS:
        deps = _dependency_rows(conn, user_id)
        for assignment_id, reviewer_id, faculty_id, assigned_by in deps["reviewer_assignments_as_reviewer"]:
            if assignment_id in PRESERVE_ASSIGNMENT_IDS:
                continue
            ops.append(
                (
                    "reviewer_assignments",
                    f"DELETE reviewer_assignments assignment_id={assignment_id} "
                    f"(reviewer_id={reviewer_id}, faculty_id={faculty_id}, assigned_by={assigned_by})",
                    (assignment_id,),
                )
            )
        for decision_id, reviewer_id in deps["review_decisions"]:
            ops.append(
                (
                    "review_decisions",
                    f"DELETE review_decisions decision_id={decision_id} reviewer_id={reviewer_id}",
                    (decision_id,),
                )
            )
        for otp_id, uid, expires_at in deps["password_reset_otps"]:
            ops.append(
                (
                    "password_reset_otps",
                    f"DELETE password_reset_otps otp_id={otp_id} user_id={uid} expires_at={expires_at}",
                    (otp_id,),
                )
            )
        for token_id, uid, purpose, expires_at in deps["password_tokens"]:
            ops.append(
                (
                    "password_tokens",
                    f"DELETE password_tokens token_id={token_id} user_id={uid} purpose={purpose}",
                    (token_id,),
                )
            )
        for faculty_id, uid in deps["faculty_profiles"]:
            ops.append(
                (
                    "faculty_profiles",
                    f"DELETE faculty_profiles faculty_id={faculty_id} user_id={uid}",
                    (faculty_id,),
                )
            )
        ops.append(
            (
                "users",
                f"DELETE users user_id={user_id} email={expected_email!r}",
                (user_id, expected_email),
            )
        )
    return ops


def _run_execute(conn: psycopg.Connection, ops: list[tuple[str, str, tuple]]) -> None:
    with conn.transaction():
        for table, _desc, params in ops:
            if table == "reviewer_assignments":
                conn.execute("DELETE FROM reviewer_assignments WHERE assignment_id = %s", (params[0],))
            elif table == "review_decisions":
                conn.execute("DELETE FROM review_decisions WHERE decision_id = %s", (params[0],))
            elif table == "password_reset_otps":
                conn.execute("DELETE FROM password_reset_otps WHERE otp_id = %s", (params[0],))
            elif table == "password_tokens":
                conn.execute("DELETE FROM password_tokens WHERE token_id = %s", (params[0],))
            elif table == "faculty_profiles":
                conn.execute("DELETE FROM faculty_profiles WHERE faculty_id = %s", (params[0],))
            elif table == "users":
                user_id, expected_email = params
                deleted = conn.execute(
                    "DELETE FROM users WHERE user_id = %s AND lower(email) = lower(%s)",
                    (user_id, expected_email),
                ).rowcount
                if deleted != 1:
                    raise RuntimeError(f"users delete affected {deleted} rows for user_id={user_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove verified pytest test accounts from development DB.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform deletion (default is dry-run only).",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help='Required with --execute: type exactly "DELETE TEST ACCOUNTS" to proceed.',
    )
    args = parser.parse_args()

    with psycopg.connect(_conninfo()) as conn:
        db_name = conn.execute("SELECT current_database()").fetchone()[0]
        print(f"Connected to database: {db_name}")
        if db_name != os.getenv("DB_NAME", "facultylink_db"):
            print("Warning: connected database name differs from DB_NAME in .env")

        errors = _validate_targets(conn)
        if errors:
            print("Validation failed:")
            for err in errors:
                print(f"  - {err}")
            return 1

        print("Target users (verified):")
        for user_id, expected_email in TARGET_USERS:
            user = _fetch_user(conn, user_id)
            print(f"  user_id={user_id} email={user['email']} role={user['role']} name={user['full_name']}")
            deps = _dependency_rows(conn, user_id)
            for key, rows in deps.items():
                if rows:
                    print(f"    {key}: {len(rows)} row(s) {rows}")

        ops = _planned_deletes(conn)
        print("\nPlanned deletes (in order):")
        if not ops:
            print("  (none)")
        for _table, desc, _params in ops:
            print(f"  - {desc}")

        print("\nPreserved:")
        print(f"  user_id 145 (Jason Baroro), reviewer_assignments ids {sorted(PRESERVE_ASSIGNMENT_IDS)}")

        if not args.execute:
            print("\nDRY RUN — no changes made. Re-run with --execute --confirm \"DELETE TEST ACCOUNTS\" to apply.")
            return 0

        if args.confirm != "DELETE TEST ACCOUNTS":
            print('Refusing --execute without --confirm "DELETE TEST ACCOUNTS"')
            return 1

        try:
            _run_execute(conn, ops)
        except Exception as exc:
            print(f"Error during deletion (transaction rolled back): {exc}")
            return 1
        print("Deletion completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
