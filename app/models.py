"""Pydantic models: the shape of every request and response.

Each resource has an *In* model (what the client sends on create/update)
and an output model (what the API returns, including the identifier).
Field names match data/examples/ and the README's field table.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal["compact", "suv", "estate"]
RentalStatus = Literal["requested", "ready", "handed_over"]


class StrictModel(BaseModel):
    # Unknown fields are rejected (422) instead of silently ignored.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------- cars ----------

class CarIn(StrictModel):
    make: str = Field(min_length=1, max_length=50, examples=["VW"])
    model: str = Field(min_length=1, max_length=50, examples=["Golf"])
    plate: str = Field(min_length=2, max_length=20, examples=["AG 123 456"])
    category: Category
    parking_spot: str = Field(min_length=1, max_length=10, examples=["B12"])


class Car(CarIn):
    car_id: int


# ---------- customers ----------

class CustomerIn(StrictModel):
    name: str = Field(min_length=1, max_length=100, examples=["Nina Keller"])
    licence_number: str = Field(min_length=3, max_length=30, examples=["CH 1234567"])


class Customer(CustomerIn):
    customer_id: int


# ---------- rentals ----------

class RentalIn(StrictModel):
    customer_id: int = Field(gt=0)
    car_id: int = Field(gt=0)
    pickup_date: date
    return_date: date
    pickup_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", examples=["09:00"])

    @model_validator(mode="after")
    def return_after_pickup(self):
        # Business rule 2: the return date must be after the pickup date.
        if self.return_date <= self.pickup_date:
            raise ValueError("return_date must be after pickup_date")
        return self


class RentalUpdate(RentalIn):
    status: RentalStatus


class Rental(RentalUpdate):
    rental_number: str


class Availability(BaseModel):
    """Free cars for a period. When the requested category is full,
    other_categories is true and cars lists what is free elsewhere (rule 3)."""

    pickup_date: date
    return_date: date
    category: Category | None
    other_categories: bool
    cars: list[Car]
