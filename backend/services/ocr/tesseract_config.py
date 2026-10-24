"""Locate Tesseract on the host and configure pytesseract (Windows-friendly)."""
from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path

_WINDOWS_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


@lru_cache(maxsize=1)
def resolve_tesseract_executable() -> str | None:
    """Return path to tesseract executable, or None if not installed."""
    env = (os.getenv("TESSERACT_CMD") or "").strip()
    if env:
        path = Path(env)
        if path.is_file():
            return str(path.resolve())

    found = shutil.which("tesseract")
    if found:
        return found

    for candidate in _WINDOWS_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def configure_pytesseract() -> bool:
    """Point pytesseract at the resolved binary. Returns True if configured."""
    cmd = resolve_tesseract_executable()
    if not cmd:
        return False
    try:
        import pytesseract
    except ImportError:
        return False
    pytesseract.pytesseract.tesseract_cmd = cmd
    return True


def tesseract_version_line() -> str | None:
    cmd = resolve_tesseract_executable()
    if not cmd:
        return None
    import subprocess

    try:
        proc = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        line = (proc.stdout or proc.stderr or "").strip().splitlines()
        return line[0] if line else None
    except (OSError, subprocess.SubprocessError):
        return None
