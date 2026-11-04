"""SQLAlchemy engine and session factory.

The database URL defaults to sqlite:///data/carrental.db relative to the
project root. Set CARRENTAL_DB_URL to override (useful for tests or
deployment).

make_engine() configures every SQLite connection the same way, for the app
and for the tests:

- Foreign-key enforcement is off by default in SQLite; a PRAGMA on every new
  connection turns it on so the constraints in orm_models are enforced.
- Each transaction starts with BEGIN IMMEDIATE, which takes SQLite's write
  lock at the start of the request instead of at its first INSERT. Two
  requests that both read the highest rental number and then insert would
  otherwise compute the same number; now the second one waits until the
  first has committed and then reads the new highest number. SQLite allows
  one writer at a time anyway, so this costs little for one rental desk;
  a waiting request gives up after BUSY_TIMEOUT seconds.
"""

import os

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from app.orm_models import Base
from app.settings import PROJECT_ROOT

BUSY_TIMEOUT = 15  # seconds a request waits for another request's transaction


def _db_url() -> str:
    if url := os.environ.get("CARRENTAL_DB_URL"):
        return url
    db_path = PROJECT_ROOT / "data" / "carrental.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def make_engine(url: str, **kwargs) -> Engine:
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": BUSY_TIMEOUT},
        **kwargs,
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record) -> None:
        # Stop the sqlite3 driver from issuing its own BEGIN, so the
        # "begin" listener below decides how each transaction starts.
        dbapi_conn.isolation_level = None
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    Base.metadata.create_all(engine)  # idempotent; creates tables on first run
    return engine


engine = make_engine(_db_url())

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
