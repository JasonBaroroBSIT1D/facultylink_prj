from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from extensions import db
from models import PasswordResetOtp, User


def _hash_otp(user_id: int, otp: str) -> str:
    pepper = current_app.config.get("SECRET_KEY", "")
    payload = f"{user_id}:{otp}:{pepper}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _otp_ttl_seconds() -> int:
    return int(current_app.config.get("OTP_TTL_SECONDS", 300))


def _otp_resend_cooldown_seconds() -> int:
    return int(current_app.config.get("OTP_RESEND_COOLDOWN_SECONDS", 60))


def _otp_max_attempts() -> int:
    return int(current_app.config.get("OTP_MAX_ATTEMPTS", 5))


def invalidate_active_otps(user: User) -> None:
    now = datetime.now(timezone.utc)
    db.session.query(PasswordResetOtp).filter(
        PasswordResetOtp.user_id == user.user_id,
        PasswordResetOtp.used_at.is_(None),
    ).update({PasswordResetOtp.used_at: now})


def issue_otp(user: User) -> tuple[str, str | None]:
    """Returns (plaintext_otp, cooldown_message). Plaintext only for email transport."""
    now = datetime.now(timezone.utc)
    active = (
        PasswordResetOtp.query.filter_by(user_id=user.user_id, used_at=None)
        .order_by(PasswordResetOtp.otp_id.desc())
        .first()
    )
    if active:
        last = active.last_sent_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = (now - last).total_seconds()
        cooldown = _otp_resend_cooldown_seconds()
        if elapsed < cooldown:
            wait = int(cooldown - elapsed)
            return "", f"Please wait {wait} seconds before requesting another code."

    invalidate_active_otps(user)
    otp = f"{secrets.randbelow(900000) + 100000:06d}"
    row = PasswordResetOtp(
        user_id=user.user_id,
        otp_hash=_hash_otp(user.user_id, otp),
        expires_at=now + timedelta(seconds=_otp_ttl_seconds()),
        failed_attempts=0,
        last_sent_at=now,
    )
    db.session.add(row)
    db.session.flush()
    return otp, None


def verify_otp(user: User, otp: str) -> tuple[bool, str | None]:
    row = (
        PasswordResetOtp.query.filter_by(user_id=user.user_id, used_at=None)
        .order_by(PasswordResetOtp.otp_id.desc())
        .first()
    )
    if not row:
        return False, "invalid_otp"
    now = datetime.now(timezone.utc)
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now >= expires:
        row.used_at = now
        return False, "expired_otp"
    if row.failed_attempts >= _otp_max_attempts():
        row.used_at = now
        return False, "too_many_attempts"
    if _hash_otp(user.user_id, otp.strip()) != row.otp_hash:
        row.failed_attempts += 1
        if row.failed_attempts >= _otp_max_attempts():
            row.used_at = now
        db.session.flush()
        return False, "invalid_otp"
    row.used_at = now
    db.session.flush()
    return True, None


def consume_otp(user: User, otp: str) -> bool:
    ok, _reason = verify_otp(user, otp)
    if not ok:
        return False
    row = (
        PasswordResetOtp.query.filter_by(user_id=user.user_id, used_at=None)
        .order_by(PasswordResetOtp.otp_id.desc())
        .first()
    )
    if not row:
        return False
    row.used_at = datetime.now(timezone.utc)
    return True


def issue_reset_grant(user: User) -> str:
    """Short-lived opaque grant after OTP verification (stored hashed)."""
    from auth.password_tokens import issue_token

    return issue_token(user, "otp_reset")
