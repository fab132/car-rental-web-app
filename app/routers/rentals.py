"""Presentation layer for rentals: HTTP in, service call, HTTP out."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_rental_service
from app.models import Rental, RentalIn, RentalStatus, RentalUpdate
from app.services import RentalService

router = APIRouter(prefix="/rentals", tags=["rentals"])

NOT_FOUND = {"description": "Rental, car or customer not found"}


@router.get("", response_model=list[Rental])
def list_rentals(status: RentalStatus | None = None,
                 service: RentalService = Depends(get_rental_service)):
    """All rentals, earliest pickup first. ?status=requested gives the yard queue."""
    return service.list(status)


@router.get("/{rental_number}", response_model=Rental, responses={404: NOT_FOUND})
def get_rental(rental_number: str, service: RentalService = Depends(get_rental_service)):
    return service.get(rental_number)


@router.post("", response_model=Rental, status_code=status.HTTP_201_CREATED,
             responses={404: NOT_FOUND, 409: {"description": "Car already rented in this period"}})
def create_rental(data: RentalIn, service: RentalService = Depends(get_rental_service)):
    """Creates a rental with status requested and the next rental number."""
    return service.create(data)


@router.put("/{rental_number}", response_model=Rental,
            responses={404: NOT_FOUND,
                       409: {"description": "Car taken, status change not allowed, or handed over"}})
def update_rental(rental_number: str, data: RentalUpdate,
                  service: RentalService = Depends(get_rental_service)):
    return service.update(rental_number, data)


@router.delete("/{rental_number}", status_code=status.HTTP_204_NO_CONTENT,
               responses={404: NOT_FOUND})
def delete_rental(rental_number: str, service: RentalService = Depends(get_rental_service)):
    service.delete(rental_number)
