"""SQLAlchemy engine and session factory.

The database URL defaults to sqlite:///data/carrental.db relative to the
project root. Set CARRENTAL_DB_URL to override (useful for tests or
deployment).

SQLite has foreign-key enforcement off by default; we turn it on with a
PRAGMA on every new connection so the FK constraints declared in orm_models
are actually enforced.
"""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.orm_models import Base
from app.settings import PROJECT_ROOT


def _db_url() -> str:
    if url := os.environ.get("CARRENTAL_DB_URL"):
        return url
    db_path = PROJECT_ROOT / "data" / "carrental.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


engine = create_engine(_db_url(), connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_conn, _record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


Base.metadata.create_all(engine)  # idempotent; creates tables on first run

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
