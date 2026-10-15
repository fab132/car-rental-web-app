"""Presentation layer for customers: HTTP in, service call, HTTP out."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_customer_service
from app.models import Customer, CustomerIn
from app.services import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])

ERRORS = {404: {"description": "Customer not found"}, 409: {"description": "Business rule broken"}}


@router.get("", response_model=list[Customer])
def list_customers(service: CustomerService = Depends(get_customer_service)):
    return service.list()


@router.get("/{customer_id}", response_model=Customer, responses={404: ERRORS[404]})
def get_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)):
    return service.get(customer_id)


@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED,
             responses={409: {"description": "Licence number already registered"}})
def create_customer(data: CustomerIn, service: CustomerService = Depends(get_customer_service)):
    return service.create(data)


@router.put("/{customer_id}", response_model=Customer, responses=ERRORS)
def update_customer(customer_id: int, data: CustomerIn,
                    service: CustomerService = Depends(get_customer_service)):
    return service.update(customer_id, data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={404: ERRORS[404], 409: {"description": "Customer has rentals"}})
def delete_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)):
    service.delete(customer_id)
