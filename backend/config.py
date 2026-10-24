import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    API_SERVICE_NAME = "FacultyLink API"

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "facultylink_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    # Pytest must set TEST_DATABASE_URL (see backend/testing_db_guard.py); not used at runtime.
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    _cors_raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8765,http://127.0.0.1:8765,http://localhost:5000",
    )
    CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]

    JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_ACCESS_TTL_SECONDS = int(os.getenv("JWT_ACCESS_TTL_SECONDS", "3600"))
    AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "facultylink_access")
    AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")
    AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
    CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "facultylink_csrf")

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    _smtp_password_raw = os.getenv("SMTP_PASSWORD", "")
    SMTP_PASSWORD = _smtp_password_raw.replace(" ", "") if _smtp_password_raw else ""
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME or "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    WEB_PORTAL_BASE_URL = os.getenv("WEB_PORTAL_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    MOBILE_APP_DEEP_LINK_BASE = os.getenv("MOBILE_APP_DEEP_LINK_BASE", "facultylink://setup").strip()
    MOBILE_SETUP_HTTPS_URL = os.getenv("MOBILE_SETUP_HTTPS_URL", "").strip()
    PASSWORD_TOKEN_TTL_HOURS = int(os.getenv("PASSWORD_TOKEN_TTL_HOURS", "72"))
    MAIL_SUPPRESS_SEND = False
    AUTH_FORGOT_PASSWORD_RATE_LIMIT = int(os.getenv("AUTH_FORGOT_PASSWORD_RATE_LIMIT", "5"))
    AUTH_FORGOT_PASSWORD_RATE_WINDOW = int(os.getenv("AUTH_FORGOT_PASSWORD_RATE_WINDOW", "900"))
    AUTH_RESEND_INVITE_RATE_LIMIT = int(os.getenv("AUTH_RESEND_INVITE_RATE_LIMIT", "10"))
    AUTH_RESEND_INVITE_RATE_WINDOW = int(os.getenv("AUTH_RESEND_INVITE_RATE_WINDOW", "3600"))
    AUTH_PASSWORD_TOKEN_RATE_LIMIT = int(os.getenv("AUTH_PASSWORD_TOKEN_RATE_LIMIT", "30"))
    AUTH_PASSWORD_TOKEN_RATE_WINDOW = int(os.getenv("AUTH_PASSWORD_TOKEN_RATE_WINDOW", "900"))
    OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "300"))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))
    OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    TEMP_PASSWORD_TTL_HOURS = int(os.getenv("TEMP_PASSWORD_TTL_HOURS", "72"))

    # Phase 1 document uploads (local storage; automatic approval disabled until Phase 2+).
    DOCUMENT_STORAGE_ROOT = os.getenv(
        "DOCUMENT_STORAGE_ROOT",
        str(_ROOT / "backend" / "storage" / "documents"),
    )
    DOCUMENT_UPLOAD_MAX_BYTES = int(os.getenv("DOCUMENT_UPLOAD_MAX_BYTES", str(25 * 1024 * 1024)))
    DOCUMENT_AUTO_APPROVAL_ENABLED = os.getenv("DOCUMENT_AUTO_APPROVAL_ENABLED", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    @staticmethod
    def smtp_configured() -> bool:
        return bool(Config.SMTP_HOST and Config.SMTP_USERNAME and Config.SMTP_PASSWORD and Config.SMTP_FROM_EMAIL)

    @staticmethod
    def psycopg_conninfo() -> str:
        return (
            f"host={Config.DB_HOST} port={Config.DB_PORT} dbname={Config.DB_NAME} "
            f"user={Config.DB_USER} password={Config.DB_PASSWORD}"
        )
