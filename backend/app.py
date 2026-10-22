from __future__ import annotations

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS

from api import register_api
from config import Config
from errors import register_error_handlers
from extensions import db


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app.logger.setLevel(logging.DEBUG if app.config.get("DEBUG") else logging.INFO)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    db.init_app(app)
    register_error_handlers(app)
    register_api(app)

    @app.get("/")
    def root():
        return jsonify(
            {
                "service": app.config.get("API_SERVICE_NAME", "FacultyLink API"),
                "version": "v1",
                "health": "/api/v1/health",
            }
        )

    return app


def main() -> None:
    app = create_app()
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
