"""Providers for FastAPI's Depends().

Routers ask for a service; these functions build it with its repositories.
Tests override get_session to inject an in-memory SQLite database instead
of the production one; everything else is unaffected.

FastAPI reuses a sub-dependency within the same request, so all three
repositories wired into one service share the same session instance.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repository import CarRepository, CustomerRepository, RentalRepository
from app.services import CarService, CustomerService, RentalService


def get_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_car_repo(session: Session = Depends(get_session)) -> CarRepository:
    return CarRepository(session)


def get_customer_repo(session: Session = Depends(get_session)) -> CustomerRepository:
    return CustomerRepository(session)


def get_rental_repo(session: Session = Depends(get_session)) -> RentalRepository:
    return RentalRepository(session)


def get_car_service(
    cars: CarRepository = Depends(get_car_repo),
    rentals: RentalRepository = Depends(get_rental_repo),
) -> CarService:
    return CarService(cars, rentals)


def get_customer_service(
    customers: CustomerRepository = Depends(get_customer_repo),
    rentals: RentalRepository = Depends(get_rental_repo),
) -> CustomerService:
    return CustomerService(customers, rentals)


def get_rental_service(
    rentals: RentalRepository = Depends(get_rental_repo),
    cars: CarRepository = Depends(get_car_repo),
    customers: CustomerRepository = Depends(get_customer_repo),
) -> RentalService:
    return RentalService(rentals, cars, customers)
