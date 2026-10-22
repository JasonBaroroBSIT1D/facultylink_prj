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

    @staticmethod
    def psycopg_conninfo() -> str:
        return (
            f"host={Config.DB_HOST} port={Config.DB_PORT} dbname={Config.DB_NAME} "
            f"user={Config.DB_USER} password={Config.DB_PASSWORD}"
        )
