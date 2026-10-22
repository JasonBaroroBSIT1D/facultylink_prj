from __future__ import annotations

from flask import Flask, jsonify


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "not_found", "message": "The requested resource was not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "method_not_allowed", "message": "Method not allowed for this URL."}), 405

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "internal_error", "message": "An unexpected server error occurred."}), 500
