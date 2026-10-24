from __future__ import annotations

import re


def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "password_too_short"
    if not re.search(r"[A-Za-z]", password):
        return "password_needs_letter"
    if not re.search(r"\d", password):
        return "password_needs_digit"
    return None


def password_validation_message(code: str | None) -> str:
    messages = {
        "password_too_short": "Password must be at least 8 characters.",
        "password_needs_letter": "Password must include at least one letter.",
        "password_needs_digit": "Password must include at least one number.",
    }
    return messages.get(code or "", "Password does not meet requirements.")
