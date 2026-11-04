"""Simultaneous bookings on a real SQLite file get distinct rental numbers.

Each booking runs in its own thread and session, like parallel requests in
uvicorn's thread pool. The read of the existing rentals is slowed down so the
bookings overlap: without BEGIN IMMEDIATE they all compute R-106 and all but
one fail on the primary key.
"""

import threading
import time

from sqlalchemy.orm import sessionmaker

from app.database import make_engine
from app.models import RentalIn
from app.orm_models import RentalRow
from app.repository import CarRepository, CustomerRepository, RentalRepository
from app.services import RentalService
from tests.conftest import _seed


def test_parallel_bookings_get_distinct_rental_numbers(tmp_path, monkeypatch):
    engine = make_engine(f"sqlite:///{tmp_path / 'race.db'}")
    Session = sessionmaker(bind=engine)

    original_all = RentalRepository.all

    def slow_all(self):
        rows = original_all(self)
        time.sleep(0.2)
        return rows

    monkeypatch.setattr(RentalRepository, "all", slow_all)

    with Session() as seed_session:
        _seed(seed_session)

    results, errors = [], []

    def book(car_id: int) -> None:
        with Session() as session:
            try:
                service = RentalService(RentalRepository(session), CarRepository(session),
                                        CustomerRepository(session))
                rental = service.create(RentalIn(customer_id=1, car_id=car_id,
                                                 pickup_date="2027-03-01",
                                                 return_date="2027-03-03",
                                                 pickup_time="09:00"))
                session.commit()
                results.append(rental.rental_number)
            except Exception as exc:  # collected and asserted below
                session.rollback()
                errors.append(exc)

    threads = [threading.Thread(target=book, args=(car_id,)) for car_id in (1, 2, 3, 4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert sorted(results) == ["R-106", "R-107", "R-108", "R-109"]
    with Session() as session:
        assert session.query(RentalRow).count() == 8
    engine.dispose()
