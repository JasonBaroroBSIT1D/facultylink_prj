"""Build ledger credit slot keys from indicator credit_uniqueness policy."""
from __future__ import annotations

PER_EVIDENCE_HASH = "per_evidence_hash"
ONE_ACTIVE_CREDIT_PER_TERM = "one_active_credit_per_term"

MODES = frozenset({PER_EVIDENCE_HASH, ONE_ACTIVE_CREDIT_PER_TERM})


def build_credit_uniqueness_key(
    *,
    mode: str,
    faculty_id: int,
    indicator_id: int,
    academic_year: str,
    semester: str,
    evidence_sha256: str | None,
) -> str:
    if mode not in MODES:
        raise ValueError(f"Unsupported credit_uniqueness mode: {mode}")
    slot = f"f{faculty_id}:i{indicator_id}:{academic_year}:{semester}"
    if mode == ONE_ACTIVE_CREDIT_PER_TERM:
        return slot
    if not evidence_sha256:
        raise ValueError("evidence_sha256 is required for per_evidence_hash credit slots.")
    return f"{slot}:h{evidence_sha256}"
