"""Send one real welcome-credentials test email via Gmail SMTP (optional).

Set SMTP_TEST_RECIPIENT in .env to an authorized inbox before running.
Does not print SMTP passwords or message tokens.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from auth.mailer import MailDeliveryError, send_welcome_credentials_email  # noqa: E402
from auth.temp_password import generate_temporary_password  # noqa: E402
from config import Config  # noqa: E402
import os  # noqa: E402
import secrets  # noqa: E402


def main() -> int:
    recipient = (os.getenv("SMTP_TEST_RECIPIENT") or "").strip()
    if not recipient:
        print("Skip: set SMTP_TEST_RECIPIENT in .env to run a live SMTP delivery test.")
        return 0
    if not Config.smtp_configured():
        print("ERROR: SMTP is not fully configured in .env.", file=sys.stderr)
        return 1

    app = create_app(Config)
    temp = generate_temporary_password()
    with app.app_context():
        try:
            send_welcome_credentials_email(
                to_email=recipient,
                full_name="SMTP Test",
                role="faculty",
                temporary_password=temp,
            )
        except MailDeliveryError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1

    print(f"OK: Live SMTP test message sent to {recipient}. Check the inbox (and spam).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
