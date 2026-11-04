"""Project paths.

The database location is configured in app/database.py (CARRENTAL_DB_URL,
default data/carrental.db). data/examples/ holds the seed data that
scripts/seed.py loads and the tests use.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "data" / "examples"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
STATIC_DIR = PROJECT_ROOT / "app" / "static"
