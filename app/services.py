"""Service layer: the business rules.

Routers call these classes; these classes call the repositories.
Every rule from README section 2 "Business rules" that the API enforces
lives here, so there is exactly one place to read and test them.
"""

from datetime import date

from app.errors import ConflictError, NotFoundError
from app.models import (Availability, Car, CarIn, Category, Customer, CustomerIn,
                        Rental, RentalIn, RentalUpdate)
from app.repository import JsonRepository


def _next_int(field: str):
    return lambda records: max((r[field] for r in records), default=0) + 1


def _next_rental_number(records: list[dict]) -> str:
    # Rental numbers continue from the highest existing one: R-105 -> R-106.
    highest = max((int(r["rental_number"].split("-")[1]) for r in records), default=100)
    return f"R-{highest + 1}"


def periods_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    # A car returned on a day can be picked up again that same day.
    return a_start < b_end and b_start < a_end


# Allowed status changes. Forward along the workflow, plus ready -> requested
# so a car marked ready by mistake can go back into the yard queue.
# A handed-over rental is final in version 1.
ALLOWED_STATUS_CHANGES = {
    "requested": {"requested", "ready"},
    "ready": {"ready", "requested", "handed_over"},
    "handed_over": {"handed_over"},
}


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


class RentalService:
    def __init__(self, rentals: JsonRepository, cars: JsonRepository, customers: JsonRepository):
        self.rentals = rentals
        self.cars = cars
        self.customers = customers

    def list(self, status: str | None = None) -> list[Rental]:
        records = self.rentals.all()
        if status is not None:
            records = [r for r in records if r["status"] == status]
        # Earliest pickup first: the order Luca works the yard queue in.
        records.sort(key=lambda r: (r["pickup_date"], r["pickup_time"]))
        return [Rental(**r) for r in records]

    def get(self, rental_number: str) -> Rental:
        record = self.rentals.get(rental_number.upper())
        if record is None:
            raise NotFoundError(f"Rental {rental_number} not found")
        return Rental(**record)

    # ----- rules -----

    def _check_references(self, data: RentalIn) -> None:
        if self.customers.get(data.customer_id) is None:
            raise NotFoundError(f"Customer {data.customer_id} not found")
        if self.cars.get(data.car_id) is None:
            raise NotFoundError(f"Car {data.car_id} not found")

    def _blocking_rental(self, car_id: int, start: date, end: date,
                         ignore: str | None = None) -> str | None:
        for r in self.rentals.all():
            if r["car_id"] != car_id or r["rental_number"] == ignore:
                continue
            if periods_overlap(start, end, date.fromisoformat(r["pickup_date"]),
                               date.fromisoformat(r["return_date"])):
                return r["rental_number"]
        return None

    def _check_car_free(self, data: RentalIn, ignore: str | None = None) -> None:
        # Rule 3: a car is rented to one customer at a time.
        blocking = self._blocking_rental(data.car_id, data.pickup_date, data.return_date, ignore)
        if blocking:
            raise ConflictError(
                f"Car {data.car_id} is already rented in this period (rental {blocking})"
            )

    # ----- queries -----

    def available(self, pickup_date: date, return_date: date,
                  category: Category | None = None) -> Availability:
        free = [Car(**c) for c in self.cars.all()
                if not self._blocking_rental(c["car_id"], pickup_date, return_date)]
        in_category = [c for c in free if category is None or c.category == category]
        other = bool(category) and not in_category
        return Availability(pickup_date=pickup_date, return_date=return_date, category=category,
                            other_categories=other, cars=free if other else in_category)

    # ----- commands -----

    def create(self, data: RentalIn) -> Rental:
        self._check_references(data)
        self._check_car_free(data)
        # Rule 4: a new rental always starts as requested.
        record = {**data.model_dump(mode="json"), "status": "requested"}
        return Rental(**self.rentals.add(record, _next_rental_number))

    def update(self, rental_number: str, data: RentalUpdate) -> Rental:
        current = self.get(rental_number)
        if current.status == "handed_over":
            raise ConflictError(f"Rental {current.rental_number} is handed over and cannot change")
        if data.status not in ALLOWED_STATUS_CHANGES[current.status]:
            # Rule 6: only a ready rental can be handed over.
            raise ConflictError(
                f"Status cannot change from {current.status} to {data.status}"
            )
        self._check_references(data)
        self._check_car_free(data, ignore=current.rental_number)
        record = {"rental_number": current.rental_number, **data.model_dump(mode="json")}
        return Rental(**self.rentals.replace(current.rental_number, record))

    def delete(self, rental_number: str) -> None:
        current = self.get(rental_number)
        self.rentals.delete(current.rental_number)
