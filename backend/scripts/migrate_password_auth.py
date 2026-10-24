"""Apply password invitation columns/tables to an existing facultylink_db (non-destructive)."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text

from app import create_app
from config import Config
from extensions import db


def main() -> int:
    app = create_app(Config)
    with app.app_context():
        db.session.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS must_set_password BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        db.session.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS credentials_delivery_pending BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS password_reset_otps (
                    otp_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    otp_hash VARCHAR(128) NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used_at TIMESTAMPTZ,
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    last_sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS ix_password_reset_otps_user_id ON password_reset_otps (user_id)")
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS password_tokens (
                    token_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    token_hash VARCHAR(128) NOT NULL UNIQUE,
                    purpose VARCHAR(20) NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS ix_password_tokens_user_id ON password_tokens (user_id)")
        )
        db.session.execute(
            text(
                """
                UPDATE users
                SET must_set_password = FALSE, credentials_delivery_pending = FALSE
                WHERE email IN ('admin@facultylink.edu', 'reviewer@facultylink.edu', 'faculty@facultylink.edu')
                """
            )
        )
        db.session.commit()
        print("Password auth migration applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
