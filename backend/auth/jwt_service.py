from __future__ import annotations

import secrets
import threading
import time
from typing import Any

import jwt
from flask import current_app

_revoked_jti: set[str] = set()
_lock = threading.Lock()


class TokenError(Exception):
    pass


def create_access_token(user_id: int, role: str, email: str, full_name: str) -> tuple[str, int]:
    ttl = int(current_app.config["JWT_ACCESS_TTL_SECONDS"])
    now = int(time.time())
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "name": full_name,
        "iat": now,
        "exp": now + ttl,
        "jti": jti,
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")
    return token, ttl


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid_token") from exc

    jti = payload.get("jti")
    if not jti:
        raise TokenError("invalid_token")
    with _lock:
        if jti in _revoked_jti:
            raise TokenError("token_revoked")
    return payload


def revoke_token(token: str) -> None:
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return
    jti = payload.get("jti")
    if not jti:
        return
    with _lock:
        _revoked_jti.add(jti)


def clear_revoked_for_tests() -> None:
    with _lock:
        _revoked_jti.clear()
