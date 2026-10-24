from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from extensions import db
from models import PasswordToken, User


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ttl_hours() -> int:
    return int(current_app.config.get("PASSWORD_TOKEN_TTL_HOURS", 72))


def issue_token(user: User, purpose: str) -> str:
    if purpose not in ("invite", "reset", "otp_reset"):
        raise ValueError("Invalid token purpose.")
    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_ttl_hours())
    db.session.query(PasswordToken).filter(
        PasswordToken.user_id == user.user_id,
        PasswordToken.purpose == purpose,
        PasswordToken.used_at.is_(None),
    ).update({PasswordToken.used_at: datetime.now(timezone.utc)})
    row = PasswordToken(
        user_id=user.user_id,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.session.add(row)
    db.session.flush()
    return raw


def validate_raw_token(raw: str, purpose: str | None = None) -> PasswordToken | None:
    if not raw or len(raw) < 20:
        return None
    token_hash = _hash_token(raw)
    query = PasswordToken.query.filter_by(token_hash=token_hash, used_at=None)
    if purpose:
        query = query.filter_by(purpose=purpose)
    row = query.first()
    if not row:
        return None
    now = datetime.now(timezone.utc)
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now >= expires:
        return None
    return row


def consume_token(row: PasswordToken) -> None:
    row.used_at = datetime.now(timezone.utc)
