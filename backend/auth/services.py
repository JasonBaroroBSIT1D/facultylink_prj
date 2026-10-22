from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import FacultyProfile, User


def authenticate(email: str, password: str) -> tuple[User | None, str | None]:
    normalized = email.strip().lower()
    user = User.query.filter_by(email=normalized).first()
    if not user:
        return None, "invalid_credentials"
    if not user.is_active:
        return None, "account_inactive"
    if not check_password_hash(user.password_hash, password):
        return None, "invalid_credentials"
    return user, None


def change_user_password(user: User, current_password: str, new_password: str) -> str | None:
    if not check_password_hash(user.password_hash, current_password):
        return "invalid_current_password"
    if len(new_password) < 8:
        return "password_too_short"
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return None


def create_user_account(
    *,
    email: str,
    password: str,
    role: str,
    full_name: str,
    employee_number: str | None = None,
    college: str | None = None,
    department: str | None = None,
    current_rank: str | None = None,
) -> tuple[User | None, str | None]:
    normalized = email.strip().lower()
    if User.query.filter_by(email=normalized).first():
        return None, "duplicate_email"
    if role not in ("faculty", "reviewer"):
        return None, "invalid_role"
    if len(password) < 8:
        return None, "password_too_short"

    user = User(
        email=normalized,
        password_hash=generate_password_hash(password),
        role=role,
        full_name=full_name.strip(),
        is_active=True,
    )
    db.session.add(user)
    db.session.flush()

    if role == "faculty":
        if not employee_number or not employee_number.strip():
            db.session.rollback()
            return None, "employee_number_required"
        if FacultyProfile.query.filter_by(employee_number=employee_number.strip()).first():
            db.session.rollback()
            return None, "duplicate_employee_number"
        profile = FacultyProfile(
            user_id=user.user_id,
            employee_number=employee_number.strip(),
            college=college,
            department=department,
            current_rank=current_rank,
        )
        db.session.add(profile)

    db.session.commit()
    return user, None
