"""Simple in-memory rate limiting for sensitive public auth endpoints."""
from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import current_app, jsonify, request

_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)


def _client_key(suffix: str = "") -> str:
    ip = (request.remote_addr or "unknown").strip()
    if suffix:
        return f"{ip}:{suffix}"
    return ip


def rate_limit(
    scope: str,
    *,
    max_calls: int | None = None,
    window_seconds: int | None = None,
    max_calls_config: str | None = None,
    window_config: str | None = None,
    key_suffix: Callable[[], str] | None = None,
):
    """Limit requests per IP (optional extra key from key_suffix). Disabled when TESTING=True."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_app.config.get("TESTING"):
                return view(*args, **kwargs)
            limit = max_calls
            window = window_seconds
            if max_calls_config:
                limit = int(current_app.config.get(max_calls_config, limit or 5))
            if window_config:
                window = int(current_app.config.get(window_config, window or 900))
            limit = limit or 5
            window = window or 900
            extra = key_suffix() if key_suffix else ""
            bucket_id = (scope, _client_key(extra))
            now = time.time()
            window_start = now - window
            hits = [t for t in _buckets[bucket_id] if t >= window_start]
            if len(hits) >= limit:
                return (
                    jsonify(
                        {
                            "error": "rate_limited",
                            "message": "Too many requests. Please wait and try again.",
                        }
                    ),
                    429,
                )
            hits.append(now)
            _buckets[bucket_id] = hits
            return view(*args, **kwargs)

        return wrapped

    return decorator


def clear_rate_limits_for_tests() -> None:
    _buckets.clear()
