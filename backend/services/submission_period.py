"""Evaluation-period submission gates (server-side)."""
from __future__ import annotations

from datetime import datetime, timezone

from models.evaluation_period import EvaluationPeriod


def submissions_allowed(period: EvaluationPeriod, now: datetime | None = None) -> bool:
    """Match mobile/web [opensAt, closesAt) window and submission_enabled flag."""
    now = now or datetime.now(timezone.utc)
    opens = period.opens_at if period.opens_at.tzinfo else period.opens_at.replace(tzinfo=timezone.utc)
    closes = period.closes_at if period.closes_at.tzinfo else period.closes_at.replace(tzinfo=timezone.utc)
    if now < opens or now >= closes:
        return False
    return bool(period.submission_enabled)


def submission_block_message(period: EvaluationPeriod, now: datetime | None = None) -> str | None:
    now = now or datetime.now(timezone.utc)
    opens = period.opens_at if period.opens_at.tzinfo else period.opens_at.replace(tzinfo=timezone.utc)
    closes = period.closes_at if period.closes_at.tzinfo else period.closes_at.replace(tzinfo=timezone.utc)
    if now < opens:
        return "The evaluation period has not opened yet."
    if now >= closes:
        return "The submission window has ended."
    if not period.submission_enabled:
        return "Submissions are disabled for this evaluation period."
    return None
