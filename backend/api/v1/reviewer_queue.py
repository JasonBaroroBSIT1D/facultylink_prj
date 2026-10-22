"""Reviewer document queue counts from PostgreSQL.

Queue = distinct documents for actively assigned faculty where:
- documents.status is ``needs_verification`` (reviewer verification step in schema), and
- the latest review_decisions row is not a terminal decision (``approved`` or ``rejected``).

Documents in other statuses (e.g. uploaded, processing) are not counted until the upload/OCR
pipeline marks them ``needs_verification``. Multiple decisions per document use the newest
``decided_at`` only (no join duplication in the count).
"""
from __future__ import annotations

from sqlalchemy import bindparam, text

from extensions import db

_QUEUE_SQL = text(
    """
    WITH assigned AS (
        SELECT reviewer_id, faculty_id
        FROM reviewer_assignments
        WHERE is_active = TRUE
          AND reviewer_id IN :reviewer_ids
    ),
    latest_decisions AS (
        SELECT DISTINCT ON (document_id) document_id, decision
        FROM review_decisions
        ORDER BY document_id, decided_at DESC
    )
    SELECT a.reviewer_id, COUNT(DISTINCT d.document_id) AS queue_count
    FROM assigned a
    INNER JOIN documents d ON d.faculty_id = a.faculty_id
    LEFT JOIN latest_decisions ld ON ld.document_id = d.document_id
    WHERE d.status = 'needs_verification'
      AND (ld.decision IS NULL OR ld.decision NOT IN ('approved', 'rejected'))
    GROUP BY a.reviewer_id
    """
).bindparams(bindparam("reviewer_ids", expanding=True))


def queue_counts_for_reviewers(reviewer_ids: list[int]) -> dict[int, int]:
    if not reviewer_ids:
        return {}
    rows = db.session.execute(_QUEUE_SQL, {"reviewer_ids": reviewer_ids}).all()
    counts = {int(reviewer_id): int(count) for reviewer_id, count in rows}
    return {rid: counts.get(rid, 0) for rid in reviewer_ids}


def queue_count_for_reviewer(reviewer_id: int) -> int:
    return queue_counts_for_reviewers([reviewer_id]).get(reviewer_id, 0)
