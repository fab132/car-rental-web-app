"""Every test gets a fresh in-memory SQLite database, seeded from
data/examples/, so tests never touch the production database and never
depend on each other."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_session
from app.main import app
from app.orm_models import Base, CarRow, CustomerRow, RentalRow
from app.settings import EXAMPLES_DIR


def _make_test_engine():
    # StaticPool reuses one connection so the in-memory database persists
    # across all sessions within the same test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def _seed(session) -> None:
    cars = json.loads((EXAMPLES_DIR / "cars.json").read_text(encoding="utf-8"))
    customers = json.loads((EXAMPLES_DIR / "customers.json").read_text(encoding="utf-8"))
    rentals = json.loads((EXAMPLES_DIR / "rentals.json").read_text(encoding="utf-8"))
    for c in cars:
        session.add(CarRow(**c))
    for c in customers:
        session.add(CustomerRow(**c))
    for r in rentals:
        session.add(RentalRow(**r))
    session.commit()


@pytest.fixture
def client():
    engine = _make_test_engine()
    TestSession = sessionmaker(autocommit=False, autoflush=True, bind=engine)

    seed_db = TestSession()
    _seed(seed_db)
    seed_db.close()

    def override_session():
        db = TestSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def rental_body():
    # Tom Meier rents the estate car, which is free on these dates in the example data.
    return {
        "customer_id": 2,
        "car_id": 3,
        "pickup_date": "2026-09-24",
        "return_date": "2026-09-27",
        "pickup_time": "11:00",
    }
