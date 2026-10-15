"""Presentation layer for cars: HTTP in, service call, HTTP out."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_car_service, get_rental_service
from app.models import Availability, Car, CarIn, Category
from app.services import CarService, RentalService

router = APIRouter(prefix="/cars", tags=["cars"])

ERRORS = {404: {"description": "Car not found"}, 409: {"description": "Business rule broken"}}


@router.get("", response_model=list[Car])
def list_cars(service: CarService = Depends(get_car_service)):
    return service.list()


@router.get("/available", response_model=Availability,
            responses={422: {"description": "Missing or invalid dates"}})
def available_cars(pickup_date: date, return_date: date, category: Category | None = None,
                   service: RentalService = Depends(get_rental_service)):
    """Cars free for the whole period. If the category is full, free cars
    from other categories are returned with other_categories = true."""
    if return_date <= pickup_date:
        raise HTTPException(status_code=422, detail="return_date must be after pickup_date")
    return service.available(pickup_date, return_date, category)


@router.get("/{car_id}", response_model=Car, responses={404: ERRORS[404]})
def get_car(car_id: int, service: CarService = Depends(get_car_service)):
    return service.get(car_id)


@router.post("", response_model=Car, status_code=status.HTTP_201_CREATED,
             responses={409: {"description": "Plate already registered"}})
def create_car(data: CarIn, service: CarService = Depends(get_car_service)):
    return service.create(data)


@router.put("/{car_id}", response_model=Car, responses=ERRORS)
def update_car(car_id: int, data: CarIn, service: CarService = Depends(get_car_service)):
    return service.update(car_id, data)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={404: ERRORS[404], 409: {"description": "Car is used by a rental"}})
def delete_car(car_id: int, service: CarService = Depends(get_car_service)):
    service.delete(car_id)
