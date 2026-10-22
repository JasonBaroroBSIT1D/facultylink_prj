from __future__ import annotations

from functools import wraps

from flask import current_app, jsonify, request


def validate_csrf(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("X-CSRF-Token", "")
        cookie = request.cookies.get(current_app.config["CSRF_COOKIE_NAME"], "")
        if not header or not cookie or header != cookie:
            return jsonify({"error": "csrf_failed", "message": "Invalid or missing CSRF token."}), 403
        return view(*args, **kwargs)

    return wrapped
