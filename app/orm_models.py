"""SQLAlchemy ORM table definitions.

Three tables matching the domain: cars, customers, rentals.
Row classes are only used inside repository.py; the rest of the application
works with plain dicts and Pydantic models as before.

Dates are stored as VARCHAR(10) ISO strings ("YYYY-MM-DD") so that the dict
values returned by the repositories match what services.py expects when it
calls date.fromisoformat(r["pickup_date"]).
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CarRow(Base):
    __tablename__ = "cars"

    car_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    plate: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(10), nullable=False)
    parking_spot: Mapped[str] = mapped_column(String(10), nullable=False)


class CustomerRow(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    licence_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)


class RentalRow(Base):
    __tablename__ = "rentals"

    rental_number: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.customer_id"), nullable=False
    )
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.car_id"), nullable=False
    )
    pickup_date: Mapped[str] = mapped_column(String(10), nullable=False)
    return_date: Mapped[str] = mapped_column(String(10), nullable=False)
    pickup_time: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested")
