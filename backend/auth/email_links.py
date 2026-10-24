"""Legacy token/deep-link helpers (not used for new account onboarding).

New faculty and reviewer accounts receive temporary passwords by email and sign in
through the mobile app or web login, then complete mandatory password change.
Forgot password uses OTP only. Do not use these helpers for account creation emails.
"""
from __future__ import annotations

from urllib.parse import quote

from flask import current_app


def _is_local_host_url(url: str) -> bool:
    lower = (url or "").lower()
    return any(host in lower for host in ("127.0.0.1", "localhost", "10.0.2.2", "0.0.0.0"))


def web_setup_link(token: str) -> str:
    base = current_app.config.get("WEB_PORTAL_BASE_URL", "").rstrip("/")
    return f"{base}/setup-password.html?token={quote(token)}"


def faculty_mobile_setup_link(token: str) -> str | None:
    """Prefer deep link or public HTTPS mobile setup URL; omit localhost links for devices."""
    deep_base = (current_app.config.get("MOBILE_APP_DEEP_LINK_BASE") or "").strip().rstrip("/")
    if deep_base:
        sep = "&" if "?" in deep_base else "?"
        return f"{deep_base}{sep}token={quote(token)}"

    https_mobile = (current_app.config.get("MOBILE_SETUP_HTTPS_URL") or "").strip().rstrip("/")
    if https_mobile and not _is_local_host_url(https_mobile):
        return f"{https_mobile}?token={quote(token)}"

    web = current_app.config.get("WEB_PORTAL_BASE_URL", "")
    if web and not _is_local_host_url(web):
        return web_setup_link(token)

    return None


def reviewer_setup_link(token: str) -> str | None:
    web = current_app.config.get("WEB_PORTAL_BASE_URL", "")
    if not web:
        return None
    if _is_local_host_url(web):
        return None
    return web_setup_link(token)


def manual_setup_code_instructions(token: str, *, audience: str) -> str:
    return (
        f"\nOn your {audience}, open FacultyLink and choose “Set up account” (or “Reset password”), "
        f"then paste this one-time setup code:\n\n   {token}\n\n"
        "This code expires automatically. Do not share it with anyone.\n"
    )
