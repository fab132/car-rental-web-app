"""HTML view routes for the three staff workflows and the customer status page.

These routes call the same service layer as the JSON API; they add no new
business rules.  The API routes under /cars, /customers and /rentals are
unchanged.
"""

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_car_service, get_customer_service, get_rental_service
from app.errors import ConflictError, NotFoundError
from app.models import CustomerIn, RentalIn, RentalUpdate
from app.services import CarService, CustomerService, RentalService
from app.settings import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _fmt_date(value) -> str:
    if isinstance(value, str):
        return date.fromisoformat(value).strftime("%d.%m.%Y")
    return value.strftime("%d.%m.%Y")


templates.env.filters["fmtdate"] = _fmt_date

router = APIRouter(tags=["views"])


# ---- helpers ----

def _get_or_create_customer(svc: CustomerService, name: str, licence: str) -> int:
    """Return existing customer_id for this licence, or create a new customer."""
    for c in svc.list():
        if c.licence_number.casefold() == licence.casefold():
            return c.customer_id
    return svc.create(CustomerIn(name=name, licence_number=licence)).customer_id


# ---- home ----

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active": "home"})


# ---- overview — Marco hands over keys ----

@router.get("/overview", response_class=HTMLResponse)
def overview(
    request: Request,
    note: str | None = None,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    rentals = rental_svc.list()
    cars = {c.car_id: c for c in car_svc.list()}
    customers = {c.customer_id: c for c in customer_svc.list()}
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "rentals": rentals,
        "cars": cars,
        "customers": customers,
        "note": note,
        "active": "overview",
    })


@router.post("/overview/{rental_number}/handover")
def handover(
    rental_number: str,
    rental_svc: RentalService = Depends(get_rental_service),
):
    rental = rental_svc.get(rental_number)
    rental_svc.update(rental_number, RentalUpdate(
        customer_id=rental.customer_id,
        car_id=rental.car_id,
        pickup_date=rental.pickup_date,
        return_date=rental.return_date,
        pickup_time=rental.pickup_time,
        status="handed_over",
    ))
    return RedirectResponse(f"/overview?note={rental_number} handed over", status_code=303)


# ---- yard queue — Luca fetches cars ----

@router.get("/queue", response_class=HTMLResponse)
def yard_queue(
    request: Request,
    note: str | None = None,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    rentals = rental_svc.list(status="requested")
    cars = {c.car_id: c for c in car_svc.list()}
    customers = {c.customer_id: c for c in customer_svc.list()}
    return templates.TemplateResponse("yard_queue.html", {
        "request": request,
        "rentals": rentals,
        "cars": cars,
        "customers": customers,
        "note": note,
        "active": "queue",
    })


@router.get("/queue/{rental_number}", response_class=HTMLResponse)
def rental_detail(
    rental_number: str,
    request: Request,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    try:
        rental = rental_svc.get(rental_number)
    except NotFoundError:
        return RedirectResponse("/queue", status_code=303)
    car = car_svc.get(rental.car_id)
    customer = customer_svc.get(rental.customer_id)
    return templates.TemplateResponse("rental_detail.html", {
        "request": request,
        "rental": rental,
        "car": car,
        "customer": customer,
        "active": "queue",
    })


@router.post("/queue/{rental_number}/ready")
def mark_ready(
    rental_number: str,
    rental_svc: RentalService = Depends(get_rental_service),
):
    rental = rental_svc.get(rental_number)
    rental_svc.update(rental_number, RentalUpdate(
        customer_id=rental.customer_id,
        car_id=rental.car_id,
        pickup_date=rental.pickup_date,
        return_date=rental.return_date,
        pickup_time=rental.pickup_time,
        status="ready",
    ))
    return RedirectResponse(f"/queue?note={rental_number} marked ready", status_code=303)


# ---- new rental — Marco creates a rental ----

@router.get("/new-rental", response_class=HTMLResponse)
def new_rental_form(request: Request):
    return templates.TemplateResponse("new_rental.html", {
        "request": request,
        "active": "new-rental",
    })


@router.post("/new-rental", response_class=HTMLResponse)
def new_rental_post(
    request: Request,
    name: str = Form(...),
    licence_number: str = Form(...),
    pickup_date: str = Form(...),
    return_date: str = Form(...),
    pickup_time: str = Form(...),
    category: str = Form(...),
    step: str = Form("search"),
    car_id: int = Form(None),
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    ctx = {
        "request": request,
        "active": "new-rental",
        "name": name,
        "licence_number": licence_number,
        "pickup_date": pickup_date,
        "return_date": return_date,
        "pickup_time": pickup_time,
        "category": category,
    }

    # Validate dates regardless of step.
    try:
        p = date.fromisoformat(pickup_date)
        r = date.fromisoformat(return_date)
        if r <= p:
            return templates.TemplateResponse("new_rental.html", {
                **ctx, "error_dates": "Return date must be after pickup date."
            })
    except ValueError:
        return templates.TemplateResponse("new_rental.html", {
            **ctx, "error_dates": "Enter valid dates."
        })

    if step == "search" or car_id is None:
        # Show available cars for the chosen period and category.
        availability = rental_svc.available(p, r, category)
        return templates.TemplateResponse("new_rental.html", {
            **ctx,
            "available_cars": availability.cars,
            "other_categories": availability.other_categories,
        })

    # step == "create" with a selected car — look up or create the customer then book.
    try:
        cust_id = _get_or_create_customer(customer_svc, name, licence_number)
    except ConflictError as exc:
        return templates.TemplateResponse("new_rental.html", {**ctx, "error": exc.message})

    try:
        rental = rental_svc.create(RentalIn(
            customer_id=cust_id,
            car_id=car_id,
            pickup_date=p,
            return_date=r,
            pickup_time=pickup_time,
        ))
    except (ConflictError, NotFoundError) as exc:
        # Car was just booked by someone else — show fresh availability.
        availability = rental_svc.available(p, r, category)
        return templates.TemplateResponse("new_rental.html", {
            **ctx,
            "available_cars": availability.cars,
            "other_categories": availability.other_categories,
            "error": exc.message,
        })

    return RedirectResponse(f"/new-rental/done/{rental.rental_number}", status_code=303)


@router.get("/new-rental/done/{rental_number}", response_class=HTMLResponse)
def rental_created(
    rental_number: str,
    request: Request,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    try:
        rental = rental_svc.get(rental_number)
    except NotFoundError:
        return RedirectResponse("/new-rental", status_code=303)
    car = car_svc.get(rental.car_id)
    customer = customer_svc.get(rental.customer_id)
    return templates.TemplateResponse("rental_created.html", {
        "request": request,
        "rental": rental,
        "car": car,
        "customer": customer,
        "active": "new-rental",
    })


# ---- customer status — Nina checks her rental ----

@router.get("/status", response_class=HTMLResponse)
def status_form(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})


@router.post("/status")
def status_post(rental_number: str = Form(...)):
    return RedirectResponse(f"/status/{rental_number.strip().upper()}", status_code=303)


@router.get("/status/{rental_number}", response_class=HTMLResponse)
def status_result(
    rental_number: str,
    request: Request,
    car_svc: CarService = Depends(get_car_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    try:
        rental = rental_svc.get(rental_number)
    except NotFoundError:
        return templates.TemplateResponse("status.html", {
            "request": request,
            "error": f"Rental number {rental_number} not found. Check your confirmation.",
            "rental_number": rental_number,
        })
    car = car_svc.get(rental.car_id)
    return templates.TemplateResponse("status_result.html", {
        "request": request,
        "rental": rental,
        "car": car,
    })
