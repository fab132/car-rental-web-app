"""Providers for FastAPI's Depends().

Routers ask for a service; these functions build it with its repositories.
Tests override get_data_dir to point at a temporary folder, and the ORM
step later only changes the repository built here.
"""

from pathlib import Path

from fastapi import Depends

from app.repository import JsonRepository
from app.services import CarService, CustomerService, RentalService
from app.settings import data_dir


def get_data_dir() -> Path:
    return data_dir()


def get_car_repo(d: Path = Depends(get_data_dir)) -> JsonRepository:
    return JsonRepository(d, "cars", "car_id")


def get_customer_repo(d: Path = Depends(get_data_dir)) -> JsonRepository:
    return JsonRepository(d, "customers", "customer_id")


def get_rental_repo(d: Path = Depends(get_data_dir)) -> JsonRepository:
    return JsonRepository(d, "rentals", "rental_number")


def get_car_service(
    cars: JsonRepository = Depends(get_car_repo),
    rentals: JsonRepository = Depends(get_rental_repo),
) -> CarService:
    return CarService(cars, rentals)


def get_customer_service(
    customers: JsonRepository = Depends(get_customer_repo),
    rentals: JsonRepository = Depends(get_rental_repo),
) -> CustomerService:
    return CustomerService(customers, rentals)


def get_rental_service(
    rentals: JsonRepository = Depends(get_rental_repo),
    cars: JsonRepository = Depends(get_car_repo),
    customers: JsonRepository = Depends(get_customer_repo),
) -> RentalService:
    return RentalService(rentals, cars, customers)
