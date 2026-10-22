from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from models.evaluation_period import EvaluationPeriod

MANILA = ZoneInfo("Asia/Manila")


def format_period_instant(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(MANILA)
    return local.strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"


def parse_period_instant(value: str) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=MANILA)
    return parsed.astimezone(timezone.utc)


def period_status(period: EvaluationPeriod, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    opens = period.opens_at if period.opens_at.tzinfo else period.opens_at.replace(tzinfo=timezone.utc)
    closes = period.closes_at if period.closes_at.tzinfo else period.closes_at.replace(tzinfo=timezone.utc)
    if now < opens:
        return "Upcoming"
    if now >= closes:
        return "Closed"
    return "Open"


def serialize_evaluation_period(period: EvaluationPeriod) -> dict:
    return {
        "id": str(period.period_id),
        "period_id": period.period_id,
        "period_code": period.period_code,
        "name": period.name,
        "academicYear": period.academic_year,
        "semester": period.semester,
        "opensAt": format_period_instant(period.opens_at),
        "closesAt": format_period_instant(period.closes_at),
        "timezone": period.timezone or "Asia/Manila",
        "description": period.description or "",
        "submissionEnabled": period.submission_enabled,
        "reviewEnabled": period.review_enabled,
        "status": period_status(period),
    }
