"""Live API verification against facultylink_db (reverts metadata changes)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
API = os.getenv("FACULTYLINK_VERIFY_API", "http://127.0.0.1:5000")


def _conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'facultylink_db')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def migration_005_present() -> bool:
    with psycopg.connect(_conninfo()) as conn:
        return bool(
            conn.execute(
                "SELECT to_regclass('public.kra_criterion_operational_settings') IS NOT NULL"
            ).fetchone()[0]
        )


def scoring_rules_db() -> list[dict]:
    with psycopg.connect(_conninfo()) as conn:
        rows = conn.execute(
            """
            SELECT sr.rule_id, i.indicator_code,
                   sr.rule_config->>'max_points' AS max_points,
                   sr.rule_name, sr.guideline_version
            FROM scoring_rules sr
            JOIN kra_indicators i ON i.indicator_id = sr.indicator_id
            JOIN kra_criteria c ON c.criterion_id = i.criterion_id
            JOIN kra_configurations k ON k.kra_id = c.kra_id
            WHERE k.kra_code = 'KRA I' AND c.criterion_code = 'A' AND sr.is_active = TRUE
            ORDER BY i.indicator_code
            """
        ).fetchall()
    return [
        {
            "rule_id": r[0],
            "indicator_code": r[1],
            "max_points": r[2],
            "rule_name": r[3],
            "guideline_version": r[4],
        }
        for r in rows
    ]


def admin_session() -> requests.Session:
    s = requests.Session()
    login = s.post(
        f"{API}/api/v1/auth/login",
        json={"email": "admin@facultylink.edu", "password": "demo-admin", "client_type": "web"},
        timeout=30,
    )
    login.raise_for_status()
    csrf = s.get(f"{API}/api/v1/auth/csrf", timeout=30)
    csrf.raise_for_status()
    s.headers["X-CSRF-Token"] = csrf.json()["csrf_token"]
    return s


def main() -> int:
    out: dict = {"migration_005": migration_005_present(), "scoring_rules_db": scoring_rules_db()}
    s = admin_session()

    admin_kra = s.get(f"{API}/api/v1/admin/kra-configuration", timeout=30)
    out["admin_kra_status"] = admin_kra.status_code
    if admin_kra.ok:
        body = admin_kra.json()
        out["has_kra_i_criterion_a_editing"] = body.get("kra_i_criterion_a_editing") is not None
        out["has_operational_on_kra"] = "kra_i_criterion_a_operational" in body
        editing = body.get("kra_i_criterion_a_editing") or {}
        out["locked_official"] = editing.get("locked_official")

    public = s.get(f"{API}/api/v1/kra-configuration", timeout=30)
    out["public_kra_status"] = public.status_code
    if public.ok:
        pb = public.json()
        out["public_keys"] = sorted(pb.keys())
        out["public_has_admin_editing"] = "kra_i_criterion_a_editing" in pb
        kras = pb.get("kras") or []
        if kras:
            crit_a = next(
                (c for c in (kras[0].get("criteria") or []) if c.get("code") == "A"),
                None,
            )
            out["public_criterion_a_fields"] = sorted(crit_a.keys()) if crit_a else None

    vs = s.get(f"{API}/api/v1/admin/validation-scoring/kra-i/criterion-a", timeout=30)
    out["validation_scoring_get_status"] = vs.status_code

    if admin_kra.ok and body.get("kra_i_criterion_a_editing"):
        editing = body["kra_i_criterion_a_editing"]
        orig_name = editing["criterion_name"]
        orig_desc = editing.get("description") or ""
        indicators = editing.get("indicators") or []
        marker = " [verify-revert]"
        patch_payload = {
            "criterion_name": orig_name + marker if marker not in orig_name else orig_name,
            "description": (orig_desc + marker).strip(),
            "indicators": [
                {
                    "indicator_id": ind["indicator_id"],
                    "required_evidence": (ind.get("required_evidence") or "") + marker,
                }
                for ind in indicators
            ],
        }
        patch = s.patch(
            f"{API}/api/v1/admin/kra-configuration/kra-i/criterion-a",
            json=patch_payload,
            timeout=30,
        )
        out["metadata_patch_status"] = patch.status_code
        reload = s.get(f"{API}/api/v1/admin/kra-configuration", timeout=30)
        reloaded = reload.json().get("kra_i_criterion_a_editing", {})
        out["metadata_reload_has_marker"] = marker.strip() in (reloaded.get("criterion_name") or "")

        revert = {
            "criterion_name": orig_name,
            "description": orig_desc,
            "indicators": [
                {
                    "indicator_id": ind["indicator_id"],
                    "indicator_name": ind.get("name"),
                    "required_evidence": ind.get("required_evidence"),
                }
                for ind in indicators
            ],
        }
        rev = s.patch(
            f"{API}/api/v1/admin/kra-configuration/kra-i/criterion-a",
            json=revert,
            timeout=30,
        )
        out["metadata_revert_status"] = rev.status_code

    out["scoring_rules_db_after"] = scoring_rules_db()

    if out["migration_005"] and vs.ok:
        th_patch = s.patch(
            f"{API}/api/v1/admin/validation-scoring/kra-i/criterion-a/operational-settings",
            json={"confidence_thresholds": {"field_min": 0.61}},
            timeout=30,
        )
        out["threshold_patch_status"] = th_patch.status_code
    else:
        out["threshold_patch_skipped"] = True

    print(json.dumps(out, indent=2))
    ok = (
        out.get("admin_kra_status") == 200
        and out.get("metadata_patch_status") == 200
        and out.get("metadata_revert_status") == 200
        and out.get("scoring_rules_db") == out.get("scoring_rules_db_after")
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
