from __future__ import annotations

import secrets
import string

# Avoid ambiguous characters in emailed temporary passwords.
_ALPHABET = string.ascii_letters + string.digits
_AMBIGUOUS = set("O0Il1")
_CHARS = [c for c in _ALPHABET if c not in _AMBIGUOUS]


def generate_temporary_password(length: int = 12) -> str:
    return "".join(secrets.choice(_CHARS) for _ in range(length))
