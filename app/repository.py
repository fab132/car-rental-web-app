"""Persistence layer: SQLAlchemy-backed repositories.

This is the only module that knows the data lives in a database. The service
layer works with plain dicts, so swapping JSON for SQLAlchemy touched only
this file and dependencies.py; routers, rules and tests stay the same.

Each repository exposes the same five-method interface that the service layer
expects: all(), get(), add(), replace(), delete().
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm_models import CarRow, CustomerRow, RentalRow


def _row_to_dict(row) -> dict[str, Any]:
    """Convert an ORM row to a plain dict the service layer can consume."""
    return {col.name: getattr(row, col.name) for col in row.__table__.columns}


class CarRepository:
    def __init__(self, session: Session):
        self.session = session

    def all(self) -> list[dict[str, Any]]:
        rows = self.session.execute(select(CarRow)).scalars().all()
        return [_row_to_dict(r) for r in rows]

    def get(self, car_id: int) -> dict[str, Any] | None:
        row = self.session.get(CarRow, car_id)
        return _row_to_dict(row) if row else None

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        row = CarRow(**record)
        self.session.add(row)
        self.session.flush()  # assigns the auto-incremented car_id
        return _row_to_dict(row)

    def replace(self, car_id: int, record: dict[str, Any]) -> dict[str, Any] | None:
        row = self.session.get(CarRow, car_id)
        if row is None:
            return None
        for key, value in record.items():
            setattr(row, key, value)
        self.session.flush()
        return _row_to_dict(row)

    def delete(self, car_id: int) -> bool:
        row = self.session.get(CarRow, car_id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True


class CustomerRepository:
    def __init__(self, session: Session):
        self.session = session

    def all(self) -> list[dict[str, Any]]:
        rows = self.session.execute(select(CustomerRow)).scalars().all()
        return [_row_to_dict(r) for r in rows]

    def get(self, customer_id: int) -> dict[str, Any] | None:
        row = self.session.get(CustomerRow, customer_id)
        return _row_to_dict(row) if row else None

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        row = CustomerRow(**record)
        self.session.add(row)
        self.session.flush()
        return _row_to_dict(row)

    def replace(self, customer_id: int, record: dict[str, Any]) -> dict[str, Any] | None:
        row = self.session.get(CustomerRow, customer_id)
        if row is None:
            return None
        for key, value in record.items():
            setattr(row, key, value)
        self.session.flush()
        return _row_to_dict(row)

    def delete(self, customer_id: int) -> bool:
        row = self.session.get(CustomerRow, customer_id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True


class RentalRepository:
    def __init__(self, session: Session):
        self.session = session

    def all(self) -> list[dict[str, Any]]:
        rows = self.session.execute(select(RentalRow)).scalars().all()
        return [_row_to_dict(r) for r in rows]

    def get(self, rental_number: str) -> dict[str, Any] | None:
        row = self.session.get(RentalRow, rental_number)
        return _row_to_dict(row) if row else None

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        # Rental numbers continue from the highest stored one: R-105 -> R-106.
        # Known limitation: two simultaneous bookings could compute the same
        # number; the primary key then rejects the second one (README).
        all_numbers = self.session.execute(
            select(RentalRow.rental_number)
        ).scalars().all()
        highest = max((int(n.split("-")[1]) for n in all_numbers), default=100)
        rental_number = f"R-{highest + 1}"
        row = RentalRow(rental_number=rental_number, **record)
        self.session.add(row)
        self.session.flush()
        return _row_to_dict(row)

    def replace(self, rental_number: str, record: dict[str, Any]) -> dict[str, Any] | None:
        row = self.session.get(RentalRow, rental_number)
        if row is None:
            return None
        for key, value in record.items():
            setattr(row, key, value)
        self.session.flush()
        return _row_to_dict(row)

    def delete(self, rental_number: str) -> bool:
        row = self.session.get(RentalRow, rental_number)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True
