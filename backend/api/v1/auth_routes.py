from __future__ import annotations

import secrets

from flask import Blueprint, current_app, g, jsonify, request

from auth.csrf import validate_csrf
from auth.decorators import login_required
from auth.jwt_service import create_access_token, revoke_token
from auth.mailer import MailDeliveryError, send_password_otp_email
from auth.otp_service import consume_otp, issue_otp, issue_reset_grant, verify_otp
from auth.password_policy import password_validation_message, validate_password_strength
from auth.password_tokens import validate_raw_token, consume_token
from auth.rate_limit import rate_limit
from auth.services import (
    authenticate,
    change_user_password,
    complete_mandatory_password_change,
    set_user_password,
)
from extensions import db
from models import User

bp = Blueprint("auth_v1", __name__)


def _user_payload(user: User) -> dict:
    include_profile = user.role == "faculty"
    data = user.to_public_dict(include_profile=include_profile)
    if user.role in ("reviewer", "admin"):
        data["department"] = None
    return data


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
        if reason == "temporary_password_expired":
            return jsonify(
                {
                    "error": "temporary_password_expired",
                    "message": "Your temporary password has expired. Ask an administrator to resend credentials.",
                }
            ), 403
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
    payload = {
        "user": _user_payload(user),
        "must_change_password": user.must_set_password,
    }

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
    return jsonify({"user": _user_payload(g.current_user), "must_change_password": g.current_user.must_set_password})


@bp.post("/auth/complete-mandatory-password")
@login_required
def complete_mandatory_password():
    body = request.get_json(silent=True) or {}
    temporary_password = body.get("temporary_password") or body.get("current_password") or ""
    new_password = body.get("new_password") or ""
    confirm_password = body.get("confirm_password") or new_password
    if not temporary_password or not new_password:
        return jsonify({"error": "validation_error", "message": "All password fields are required."}), 400
    if new_password != confirm_password:
        return jsonify({"error": "validation_error", "message": "New passwords do not match."}), 400

    reason = complete_mandatory_password_change(
        g.current_user,
        temporary_password=temporary_password,
        new_password=new_password,
    )
    if reason == "invalid_current_password":
        return jsonify({"error": "invalid_credentials", "message": "Temporary password is incorrect."}), 401
    if reason == "temporary_password_expired":
        return jsonify(
            {
                "error": "temporary_password_expired",
                "message": "Your temporary password has expired. Ask an administrator to resend credentials.",
            }
        ), 403
    if reason == "password_change_not_required":
        return jsonify({"error": "validation_error", "message": "Password change is not required."}), 400
    if reason == "password_same_as_temporary":
        return jsonify(
            {"error": "validation_error", "message": "Choose a new password different from the temporary password."}
        ), 400
    if reason:
        return jsonify({"error": "validation_error", "message": password_validation_message(reason)}), 400

    if getattr(g, "auth_token", None):
        revoke_token(g.auth_token)
    response = jsonify({"message": "Password updated. Please sign in again."})
    _clear_auth_cookie(response)
    return response


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
    if reason:
        return jsonify({"error": "validation_error", "message": password_validation_message(reason)}), 400

    if getattr(g, "auth_token", None):
        revoke_token(g.auth_token)
    response = jsonify({"message": "Password updated. Please sign in again."})
    _clear_auth_cookie(response)
    return response


@bp.post("/auth/forgot-password")
@rate_limit(
    "forgot_password",
    max_calls_config="AUTH_FORGOT_PASSWORD_RATE_LIMIT",
    window_config="AUTH_FORGOT_PASSWORD_RATE_WINDOW",
)
def forgot_password_request_otp():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    generic = {"message": "If an account exists for that email, a verification code has been sent."}
    if not email:
        return jsonify(generic), 200
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        return jsonify(generic), 200

    otp, cooldown = issue_otp(user)
    if cooldown:
        return jsonify({"error": "rate_limited", "message": cooldown}), 429
    db.session.commit()
    try:
        send_password_otp_email(to_email=user.email, full_name=user.full_name, otp_code=otp)
    except MailDeliveryError:
        return jsonify({**generic, "email_delivery": {"sent": False}}), 200
    return jsonify({**generic, "email_delivery": {"sent": True}}), 200


@bp.post("/auth/forgot-password/verify-otp")
@rate_limit(
    "verify_otp",
    max_calls_config="AUTH_PASSWORD_TOKEN_RATE_LIMIT",
    window_config="AUTH_PASSWORD_TOKEN_RATE_WINDOW",
)
def forgot_password_verify_otp():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    otp = (body.get("otp") or body.get("code") or "").strip()
    if not email or not otp:
        return jsonify({"error": "validation_error", "message": "Email and verification code are required."}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        return jsonify({"error": "invalid_otp", "message": "Invalid or expired verification code."}), 400

    ok, reason = verify_otp(user, otp)
    if not ok:
        messages = {
            "invalid_otp": "Invalid verification code.",
            "expired_otp": "This verification code has expired.",
            "too_many_attempts": "Too many incorrect attempts. Request a new code.",
        }
        return jsonify({"error": reason, "message": messages.get(reason, "Invalid verification code.")}), 400

    grant = issue_reset_grant(user)
    db.session.commit()
    return jsonify({"message": "Verification successful.", "reset_grant": grant}), 200


@bp.post("/auth/forgot-password/complete")
@rate_limit(
    "forgot_password_complete",
    max_calls_config="AUTH_PASSWORD_TOKEN_RATE_LIMIT",
    window_config="AUTH_PASSWORD_TOKEN_RATE_WINDOW",
)
def forgot_password_complete():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    reset_grant = (body.get("reset_grant") or "").strip()
    new_password = body.get("new_password") or ""
    confirm_password = body.get("confirm_password") or new_password
    if not email or not reset_grant or not new_password:
        return jsonify({"error": "validation_error", "message": "Missing required fields."}), 400
    if new_password != confirm_password:
        return jsonify({"error": "validation_error", "message": "Passwords do not match."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        return jsonify({"error": "invalid_grant", "message": "Unable to reset password."}), 400

    row = validate_raw_token(reset_grant, "otp_reset")
    if not row or row.user_id != user.user_id:
        return jsonify({"error": "invalid_grant", "message": "Reset authorization expired. Start again."}), 400

    policy = validate_password_strength(new_password)
    if policy:
        return jsonify({"error": "validation_error", "message": password_validation_message(policy)}), 400

    reason = set_user_password(user, new_password)
    if reason:
        return jsonify({"error": "validation_error", "message": password_validation_message(reason)}), 400
    consume_token(row)
    db.session.commit()
    return jsonify({"message": "Password updated. You can now sign in."}), 200


@bp.post("/auth/forgot-password/resend-otp")
@rate_limit(
    "resend_otp",
    max_calls_config="AUTH_FORGOT_PASSWORD_RATE_LIMIT",
    window_config="AUTH_FORGOT_PASSWORD_RATE_WINDOW",
)
def forgot_password_resend_otp():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    generic = {"message": "If an account exists for that email, a verification code has been sent."}
    if not email:
        return jsonify(generic), 200
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        return jsonify(generic), 200
    otp, cooldown = issue_otp(user)
    if cooldown:
        return jsonify({"error": "rate_limited", "message": cooldown}), 429
    db.session.commit()
    try:
        send_password_otp_email(to_email=user.email, full_name=user.full_name, otp_code=otp)
    except MailDeliveryError:
        return jsonify({**generic, "email_delivery": {"sent": False}}), 200
    return jsonify({**generic, "email_delivery": {"sent": True}}), 200
