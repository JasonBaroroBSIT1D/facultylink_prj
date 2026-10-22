"""
API v1 route registration.

Future modules (Phase 4.3+): authentication, users, faculty, reviewers,
evaluation_periods, documents, ocr, validation, kra, rank_simulation,
notifications, audit_logs.
"""
from flask import Flask

from .admin_reviewer_assignments import bp as admin_reviewer_assignments_bp
from .admin_users import bp as admin_users_bp
from .auth_routes import bp as auth_bp
from .evaluation_periods import bp as evaluation_periods_bp
from .health import bp as health_bp
from .reviewer_assignments import bp as reviewer_assignments_bp


def register_v1_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_users_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_reviewer_assignments_bp, url_prefix="/api/v1")
    app.register_blueprint(reviewer_assignments_bp, url_prefix="/api/v1")
    app.register_blueprint(evaluation_periods_bp, url_prefix="/api/v1")
