from flask import Flask

from .v1 import register_v1_blueprints


def register_api(app: Flask) -> None:
    register_v1_blueprints(app)
