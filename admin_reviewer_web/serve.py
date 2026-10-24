#!/usr/bin/env python3
"""Serve the Admin & Reviewer static frontend and proxy /api/v1 to Flask."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
ROOT = Path(__file__).resolve().parent
FLASK_BACKEND = os.getenv("FACULTYLINK_FLASK_BACKEND", "http://127.0.0.1:5000")

_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)

_FORWARD_REQUEST_HEADERS = frozenset(
    {
        "Content-Type",
        "Accept",
        "Cookie",
        "X-CSRF-Token",
        "Authorization",
    }
)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        if self.path.endswith((".js", ".html")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _proxy_api(self) -> None:
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/v1"):
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(content_length) if content_length else None

        headers = {}
        for name in _FORWARD_REQUEST_HEADERS:
            value = self.headers.get(name)
            if value:
                headers[name] = value

        url = FLASK_BACKEND + self.path
        request = urllib.request.Request(url, data=body, headers=headers, method=self.command)

        try:
            with urllib.request.urlopen(request, timeout=120) as upstream:
                self.send_response(upstream.status)
                for key, value in upstream.headers.items():
                    lowered = key.lower()
                    if lowered in _HOP_BY_HOP:
                        continue
                    self.send_header(key, value)
                self.end_headers()
                while True:
                    chunk = upstream.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                lowered = key.lower()
                if lowered in _HOP_BY_HOP:
                    continue
                self.send_header(key, value)
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except urllib.error.URLError:
            self.send_error(502, "FacultyLink API is not reachable. Start python run.py from the project root.")

    def do_OPTIONS(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-CSRF-Token")
            self.end_headers()
            return
        self.send_error(405)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self._proxy_api()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self._proxy_api()
        else:
            self.send_error(405)

    def do_PATCH(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self._proxy_api()
        else:
            self.send_error(405)

    def do_PUT(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self._proxy_api()
        else:
            self.send_error(405)

    def do_DELETE(self) -> None:
        if self.path.split("?", 1)[0].startswith("/api/v1"):
            self._proxy_api()
        else:
            self.send_error(405)


if __name__ == "__main__":
    with ThreadingHTTPServer(("", PORT), Handler) as httpd:
        print(f"FacultyLink Admin & Reviewer portal: http://127.0.0.1:{PORT}/")
        print(f"  (API proxied at /api/v1 → {FLASK_BACKEND})")
        httpd.serve_forever()
