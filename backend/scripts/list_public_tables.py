from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv

load_dotenv(BACKEND.parent / ".env")
from sqlalchemy import text
from app import create_app
from config import Config
from db.schema import EXPECTED_TABLES

app = create_app(Config)
with app.app_context():
    from extensions import db

    rows = db.session.execute(
        text(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
    ).all()
    names = [r[0] for r in rows]
    print("tables:", names)
    print("extra:", sorted(set(names) - EXPECTED_TABLES))
    print("missing:", sorted(EXPECTED_TABLES - set(names)))
