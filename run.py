#!/usr/bin/env python3
"""Start FacultyLink Flask API and Admin/Reviewer web portal together."""

from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
WEB_DIR = ROOT / "admin_reviewer_web"

API_URL = "http://127.0.0.1:5000"
WEB_URL = "http://127.0.0.1:8765"

_processes: list[subprocess.Popen] = []


def _start(name: str, cwd: Path, script: str) -> subprocess.Popen:
    print(f"Starting {name}…")
    proc = subprocess.Popen(
        [sys.executable, script],
        cwd=str(cwd),
    )
    _processes.append(proc)
    return proc


def _shutdown(signum=None, frame=None) -> None:
    del signum, frame
    if not _processes:
        return
    print("\nShutting down FacultyLink services…")
    for proc in _processes:
        if proc.poll() is None:
            proc.terminate()
    deadline = time.time() + 8
    for proc in _processes:
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
    for proc in _processes:
        if proc.poll() is None:
            proc.kill()
    _processes.clear()
    print("Stopped.")
    raise SystemExit(0)


def main() -> None:
    if not (BACKEND_DIR / "app.py").is_file():
        print("ERROR: backend/app.py not found.", file=sys.stderr)
        sys.exit(1)
    if not (WEB_DIR / "serve.py").is_file():
        print("ERROR: admin_reviewer_web/serve.py not found.", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _shutdown)

    import socket

    def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            return sock.connect_ex((host, port)) == 0

    if _port_in_use(5000) or _port_in_use(8765):
        print(
            "ERROR: Port 5000 and/or 8765 is already in use.\n"
            "  Stop every other FacultyLink process (Ctrl+C on old terminals, or Task Manager),\n"
            "  then run python run.py once.",
            file=sys.stderr,
        )
        sys.exit(1)

    api = _start("Flask API", BACKEND_DIR, "app.py")
    web = _start("Admin/Reviewer web", WEB_DIR, "serve.py")

    time.sleep(0.8)
    for label, proc in (("Flask API", api), ("Admin/Reviewer web", web)):
        code = proc.poll()
        if code is not None:
            print(f"ERROR: {label} exited immediately with code {code}.", file=sys.stderr)
            _shutdown()
            sys.exit(code or 1)

    print("")
    print("FacultyLink is running (PostgreSQL must be started separately).")
    print(f"  API:              {API_URL}")
    print(f"  Admin & Reviewer: {WEB_URL}/login.html")
    print("  (Web server proxies /api/v1 to Flask — use only this URL for sign-in.)")
    print("")
    print("Press Ctrl+C to stop both services.")
    print("You can still run backend and web individually with:")
    print("  cd backend && python app.py")
    print("  cd admin_reviewer_web && python serve.py")

    while True:
        for label, proc in (("Flask API", api), ("Admin/Reviewer web", web)):
            code = proc.poll()
            if code is not None:
                print(f"\nERROR: {label} stopped unexpectedly (exit {code}).", file=sys.stderr)
                _shutdown()
                sys.exit(code or 1)
        time.sleep(1)


if __name__ == "__main__":
    main()
