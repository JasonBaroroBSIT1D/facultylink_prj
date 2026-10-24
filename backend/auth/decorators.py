from __future__ import annotations

from functools import wraps

from flask import current_app, g, jsonify, request

from auth.jwt_service import TokenError, decode_access_token
from extensions import db
from models import User


def _extract_bearer() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def _load_user_from_token() -> User | None:
    token = request.cookies.get(current_app.config["AUTH_COOKIE_NAME"]) or _extract_bearer()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except TokenError:
        return None
    user = db.session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return None
    if user.role != payload.get("role") or user.email != payload.get("email"):
        return None
    return user


_PASSWORD_CHANGE_ALLOWED = frozenset(
    {
        "auth_v1.me",
        "auth_v1.logout",
        "auth_v1.complete_mandatory_password",
        "auth_v1.csrf_token",
    }
)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_user_from_token()
        if not user:
            return jsonify({"error": "unauthorized", "message": "Authentication required."}), 401
        g.current_user = user
        g.auth_token = request.cookies.get(current_app.config["AUTH_COOKIE_NAME"]) or _extract_bearer()
        if user.must_set_password and request.endpoint not in _PASSWORD_CHANGE_ALLOWED:
            return (
                jsonify(
                    {
                        "error": "password_change_required",
                        "message": "You must change your temporary password before continuing.",
                    }
                ),
                403,
            )
        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.current_user.role not in roles:
                return jsonify({"error": "forbidden", "message": "You do not have permission for this action."}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator
