"""Presentation layer for cars: HTTP in, service call, HTTP out."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_car_service
from app.models import Car, CarIn
from app.services import CarService

router = APIRouter(prefix="/cars", tags=["cars"])

ERRORS = {404: {"description": "Car not found"}, 409: {"description": "Business rule broken"}}


@router.get("", response_model=list[Car])
def list_cars(service: CarService = Depends(get_car_service)):
    return service.list()


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
