#!/usr/bin/env python3
"""Serve the Admin & Reviewer static frontend (no npm required)."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
ROOT = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


if __name__ == '__main__':
    with ThreadingHTTPServer(('', PORT), Handler) as httpd:
        print(f'FacultyLink Admin & Reviewer portal: http://localhost:{PORT}/')
        httpd.serve_forever()
