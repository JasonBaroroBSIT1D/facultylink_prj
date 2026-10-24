from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from auth.password_policy import validate_password_strength
from auth.temp_password import generate_temporary_password
from extensions import db
from models import FacultyProfile, User


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def temporary_password_expired(user: User) -> bool:
    if not user.must_set_password:
        return False
    ttl_hours = int(current_app.config.get("TEMP_PASSWORD_TTL_HOURS", 72))
    reference = _as_utc(user.updated_at or user.created_at)
    return datetime.now(timezone.utc) >= reference + timedelta(hours=ttl_hours)


def authenticate(email: str, password: str) -> tuple[User | None, str | None]:
    normalized = email.strip().lower()
    user = User.query.filter_by(email=normalized).first()
    if not user:
        return None, "invalid_credentials"
    if not user.is_active:
        return None, "account_inactive"
    if temporary_password_expired(user):
        return None, "temporary_password_expired"
    if not check_password_hash(user.password_hash, password):
        return None, "invalid_credentials"
    return user, None


def complete_mandatory_password_change(
    user: User, *, temporary_password: str, new_password: str
) -> str | None:
    if not user.must_set_password:
        return "password_change_not_required"
    if temporary_password_expired(user):
        return "temporary_password_expired"
    if not check_password_hash(user.password_hash, temporary_password):
        return "invalid_current_password"
    if temporary_password == new_password:
        return "password_same_as_temporary"
    policy = validate_password_strength(new_password)
    if policy:
        return policy
    user.password_hash = generate_password_hash(new_password)
    user.must_set_password = False
    user.credentials_delivery_pending = False
    db.session.commit()
    return None


def set_user_password(user: User, new_password: str) -> str | None:
    policy = validate_password_strength(new_password)
    if policy:
        return policy
    user.password_hash = generate_password_hash(new_password)
    user.must_set_password = False
    user.credentials_delivery_pending = False
    db.session.commit()
    return None


def change_user_password(user: User, current_password: str, new_password: str) -> str | None:
    if not check_password_hash(user.password_hash, current_password):
        return "invalid_current_password"
    policy = validate_password_strength(new_password)
    if policy:
        return policy
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return None


def create_user_account(
    *,
    email: str,
    password: str | None,
    role: str,
    full_name: str,
    employee_number: str | None = None,
    college: str | None = None,
    department: str | None = None,
    current_rank: str | None = None,
) -> tuple[User | None, str | None, str | None]:
    """Returns (user, error_code, temporary_password_plaintext_for_email_only)."""
    normalized = email.strip().lower()
    if User.query.filter_by(email=normalized).first():
        return None, "duplicate_email", None
    if role not in ("faculty", "reviewer"):
        return None, "invalid_role", None

    temp_plain = (password or "").strip() or generate_temporary_password()
    if len(temp_plain) < 8:
        return None, "password_too_short", None

    user = User(
        email=normalized,
        password_hash=generate_password_hash(temp_plain),
        role=role,
        full_name=full_name.strip(),
        is_active=True,
        must_set_password=True,
        credentials_delivery_pending=True,
    )
    db.session.add(user)
    db.session.flush()

    if role == "faculty":
        emp = (employee_number or "").strip()
        if not emp:
            emp = f"FL-{user.user_id:06d}"
        if FacultyProfile.query.filter_by(employee_number=emp).first():
            db.session.rollback()
            return None, "duplicate_employee_number", None
        profile = FacultyProfile(
            user_id=user.user_id,
            employee_number=emp,
            college=college,
            department=department,
            current_rank=current_rank,
        )
        db.session.add(profile)

    db.session.commit()
    return user, None, temp_plain


def rotate_temporary_credentials(user: User) -> str:
    temp_plain = generate_temporary_password()
    user.password_hash = generate_password_hash(temp_plain)
    user.must_set_password = True
    user.credentials_delivery_pending = True
    db.session.commit()
    return temp_plain
