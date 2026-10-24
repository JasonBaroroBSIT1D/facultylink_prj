"""Local filesystem storage for faculty document uploads (Phase 1)."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

_UNSAFE = re.compile(r"[^\w.\-]+", re.ASCII)


def storage_root() -> Path:
    root = Path(current_app.config["DOCUMENT_STORAGE_ROOT"])
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_storage_key(faculty_id: int, period_id: int, original_filename: str) -> str:
    safe = secure_filename(original_filename) or "upload"
    safe = _UNSAFE.sub("_", safe)[:200]
    token = uuid.uuid4().hex[:12]
    return f"faculty/{faculty_id}/period/{period_id}/{token}_{safe}"


def absolute_path_for_key(storage_key: str) -> Path:
    root = storage_root().resolve()
    target = (root / storage_key).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("Invalid storage key.")
    return target


def save_bytes(storage_key: str, data: bytes) -> None:
    path = absolute_path_for_key(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
