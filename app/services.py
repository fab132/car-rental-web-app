"""Service layer: the business rules.

Routers call these classes; these classes call the repositories.
Every rule from README section 2 "Business rules" that the API enforces
lives here, so there is exactly one place to read and test them.
"""

from app.errors import ConflictError, NotFoundError
from app.models import Car, CarIn, Customer, CustomerIn
from app.repository import JsonRepository


def _next_int(field: str):
    return lambda records: max((r[field] for r in records), default=0) + 1


class CarService:
    def __init__(self, cars: JsonRepository, rentals: JsonRepository):
        self.cars = cars
        self.rentals = rentals

    def list(self) -> list[Car]:
        return [Car(**c) for c in self.cars.all()]

    def get(self, car_id: int) -> Car:
        record = self.cars.get(car_id)
        if record is None:
            raise NotFoundError(f"Car {car_id} not found")
        return Car(**record)

    def _check_plate_unique(self, plate: str, ignore_id: int | None = None) -> None:
        for c in self.cars.all():
            if c["plate"].casefold() == plate.casefold() and c["car_id"] != ignore_id:
                raise ConflictError(f"Plate {plate} is already registered to car {c['car_id']}")

    def create(self, data: CarIn) -> Car:
        self._check_plate_unique(data.plate)
        return Car(**self.cars.add(data.model_dump(), _next_int("car_id")))

    def update(self, car_id: int, data: CarIn) -> Car:
        self.get(car_id)
        self._check_plate_unique(data.plate, ignore_id=car_id)
        return Car(**self.cars.replace(car_id, {"car_id": car_id, **data.model_dump()}))

    def delete(self, car_id: int) -> None:
        self.get(car_id)
        used_by = [r["rental_number"] for r in self.rentals.all() if r["car_id"] == car_id]
        if used_by:
            raise ConflictError(f"Car {car_id} is used by rentals {', '.join(used_by)}")
        self.cars.delete(car_id)


class CustomerService:
    def __init__(self, customers: JsonRepository, rentals: JsonRepository):
        self.customers = customers
        self.rentals = rentals

    def list(self) -> list[Customer]:
        return [Customer(**c) for c in self.customers.all()]

    def get(self, customer_id: int) -> Customer:
        record = self.customers.get(customer_id)
        if record is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return Customer(**record)

    def _check_licence_unique(self, licence: str, ignore_id: int | None = None) -> None:
        # One record per driving licence, so a returning customer is reused
        # instead of duplicated (open question in README section 3).
        for c in self.customers.all():
            if c["licence_number"].casefold() == licence.casefold() and c["customer_id"] != ignore_id:
                raise ConflictError(
                    f"Licence {licence} already belongs to customer {c['customer_id']}"
                )

    def create(self, data: CustomerIn) -> Customer:
        self._check_licence_unique(data.licence_number)
        return Customer(**self.customers.add(data.model_dump(), _next_int("customer_id")))

    def update(self, customer_id: int, data: CustomerIn) -> Customer:
        self.get(customer_id)
        self._check_licence_unique(data.licence_number, ignore_id=customer_id)
        return Customer(
            **self.customers.replace(customer_id, {"customer_id": customer_id, **data.model_dump()})
        )

    def delete(self, customer_id: int) -> None:
        self.get(customer_id)
        used_by = [r["rental_number"] for r in self.rentals.all() if r["customer_id"] == customer_id]
        if used_by:
            raise ConflictError(f"Customer {customer_id} has rentals {', '.join(used_by)}")
        self.customers.delete(customer_id)
