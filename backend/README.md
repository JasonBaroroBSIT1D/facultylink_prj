# FacultyLink — Flask REST API (Phase 4.2)

Shared backend for Admin Web, Reviewer Web, and Faculty Mobile.

## Setup

```powershell
cd backend
python -m pip install -r requirements.txt
```

Copy project-root `.env.example` to `.env` and set `DB_PASSWORD` (never commit `.env`).

## Run

From the `backend` directory:

```powershell
python app.py
```

Or:

```powershell
$env:FLASK_APP="wsgi:app"
python -m flask run --host 127.0.0.1 --port 5000
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | — | Service info |
| GET | `/api/v1/health` | — | Liveness + PostgreSQL + 18-table schema check |
| POST | `/api/v1/auth/login` | — | Web (HttpOnly cookie) or mobile (`access_token` JSON) |
| POST | `/api/v1/auth/logout` | Yes | Revoke token + clear cookie |
| GET | `/api/v1/auth/me` | Yes | Current user profile |
| POST | `/api/v1/auth/change-password` | Yes | Change password (revokes session) |
| GET | `/api/v1/admin/users` | Admin | List users (`?role=faculty\|reviewer\|admin\|all`) |
| POST | `/api/v1/admin/users` | Admin | Create faculty or reviewer account |
| PATCH | `/api/v1/admin/users/<id>` | Admin | Update name, active flag, password, faculty fields |

## Tests

```powershell
cd backend
python tests/test_health_api.py
python tests/test_auth_api.py
```

Web login requires the API at `http://127.0.0.1:5000` (see `admin_reviewer_web/js/apiConfig.js`).
Run **`python app.py`** alongside **`python serve.py`** for Admin/Reviewer sign-in.

Database scripts remain in `scripts/`; schema is not modified by the Flask app.
