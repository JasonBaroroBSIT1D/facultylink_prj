from __future__ import annotations

import secrets

from flask import Blueprint, current_app, g, jsonify, request

from auth.csrf import validate_csrf
from auth.decorators import login_required
from auth.jwt_service import create_access_token, revoke_token
from auth.services import authenticate, change_user_password
from models import User

bp = Blueprint("auth_v1", __name__)


def _user_payload(user: User) -> dict:
    include_profile = user.role == "faculty"
    return user.to_public_dict(include_profile=include_profile)


def _set_auth_cookie(response, token: str, max_age: int):
    response.set_cookie(
        current_app.config["AUTH_COOKIE_NAME"],
        token,
        max_age=max_age,
        httponly=True,
        secure=current_app.config["AUTH_COOKIE_SECURE"],
        samesite=current_app.config["AUTH_COOKIE_SAMESITE"],
        path="/",
    )


def _clear_auth_cookie(response):
    response.delete_cookie(
        current_app.config["AUTH_COOKIE_NAME"],
        path="/",
        samesite=current_app.config["AUTH_COOKIE_SAMESITE"],
    )


def _set_csrf_cookie(response, token: str):
    response.set_cookie(
        current_app.config["CSRF_COOKIE_NAME"],
        token,
        httponly=False,
        secure=current_app.config["AUTH_COOKIE_SECURE"],
        samesite=current_app.config["AUTH_COOKIE_SAMESITE"],
        path="/",
    )


@bp.get("/auth/csrf")
@login_required
def csrf_token():
    token = secrets.token_urlsafe(32)
    response = jsonify({"csrf_token": token})
    _set_csrf_cookie(response, token)
    return response


@bp.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    client = (body.get("client") or "web").lower()

    if not email or not password:
        return jsonify({"error": "validation_error", "message": "Email and password are required."}), 400

    user, reason = authenticate(email, password)
    if not user:
        if reason == "account_inactive":
            return jsonify({"error": "account_inactive", "message": "This account is inactive."}), 403
        return jsonify({"error": "invalid_credentials", "message": "Invalid email or password."}), 401

    if client == "web" and user.role not in ("admin", "reviewer"):
        return jsonify(
            {
                "error": "forbidden",
                "message": "Faculty accounts must sign in through the FacultyLink mobile app.",
            }
        ), 403

    if client == "mobile" and user.role != "faculty":
        return jsonify(
            {
                "error": "forbidden",
                "message": "Admin and reviewer accounts must use the web portal.",
            }
        ), 403

    token, ttl = create_access_token(user.user_id, user.role, user.email, user.full_name)
    payload = {"user": _user_payload(user)}

    if client == "mobile":
        payload["access_token"] = token
        payload["token_type"] = "Bearer"
        payload["expires_in"] = ttl
        return jsonify(payload), 200

    response = jsonify(payload)
    _set_auth_cookie(response, token, ttl)
    return response


@bp.post("/auth/logout")
@login_required
@validate_csrf
def logout():
    if getattr(g, "auth_token", None):
        revoke_token(g.auth_token)
    response = jsonify({"message": "Signed out."})
    _clear_auth_cookie(response)
    return response


@bp.get("/auth/me")
@login_required
def me():
    return jsonify({"user": _user_payload(g.current_user)})


@bp.post("/auth/change-password")
@login_required
@validate_csrf
def change_password():
    body = request.get_json(silent=True) or {}
    current_password = body.get("current_password") or ""
    new_password = body.get("new_password") or ""
    if not current_password or not new_password:
        return jsonify({"error": "validation_error", "message": "Current and new passwords are required."}), 400

    reason = change_user_password(g.current_user, current_password, new_password)
    if reason == "invalid_current_password":
        return jsonify({"error": "invalid_credentials", "message": "Current password is incorrect."}), 401
    if reason == "password_too_short":
        return jsonify({"error": "validation_error", "message": "New password must be at least 8 characters."}), 400

    if getattr(g, "auth_token", None):
        revoke_token(g.auth_token)
    response = jsonify({"message": "Password updated. Please sign in again."})
    _clear_auth_cookie(response)
    return response
