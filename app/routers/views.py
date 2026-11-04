"""HTML view routes for the three staff workflows and the customer status page.

These routes call the same service layer as the JSON API; they add no new
business rules. They are left out of the OpenAPI schema, which documents only
the API under /cars, /customers and /rentals.

Errors from the services are shown on the page (an error banner or a form
message) instead of the API's JSON error body.
"""

from datetime import date
from typing import get_args
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.dependencies import get_car_service, get_customer_service, get_rental_service
from app.errors import ConflictError, NotFoundError
from app.models import BookingIn, Category, CustomerIn, RentalStatus, RentalUpdate
from app.services import CarService, CustomerService, RentalService
from app.settings import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _fmt_date(value) -> str:
    if isinstance(value, str):
        return date.fromisoformat(value).strftime("%d.%m.%Y")
    return value.strftime("%d.%m.%Y")


templates.env.filters["fmtdate"] = _fmt_date

router = APIRouter(tags=["views"], include_in_schema=False)

CATEGORIES = get_args(Category)

FIELD_LABELS = {
    "name": "Customer name",
    "licence_number": "Licence number",
    "pickup_time": "Pickup time",
    "pickup_date": "Pickup date",
    "return_date": "Return date",
    "car_id": "Car",
}


def _render(request: Request, name: str, context: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context)


def _redirect(path: str, **params: str) -> RedirectResponse:
    query = "&".join(f"{k}={quote(v)}" for k, v in params.items())
    return RedirectResponse(f"{path}?{query}" if query else path, status_code=303)


def _validation_message(exc: ValidationError) -> str:
    """Turn the first Pydantic error into one sentence for the form."""
    err = exc.errors()[0]
    field = next((str(p) for p in reversed(err["loc"]) if str(p) in FIELD_LABELS), None)
    message = err["msg"].removeprefix("Value error, ")
    if err["type"] == "string_pattern_mismatch":
        message = "use the format HH:MM, e.g. 09:00"
    if "return_date must be after pickup_date" in message:
        return "Return date must be after pickup date."
    return f"{FIELD_LABELS[field]}: {message}." if field else f"{message}."


def _change_status(rental_svc: RentalService, rental_number: str,
                   status: RentalStatus) -> None:
    rental = rental_svc.get(rental_number)
    rental_svc.update(rental_number, RentalUpdate(
        customer_id=rental.customer_id,
        car_id=rental.car_id,
        pickup_date=rental.pickup_date,
        return_date=rental.return_date,
        pickup_time=rental.pickup_time,
        status=status,
    ))


# ---- home ----

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _render(request, "home.html", {"active": "home"})


# ---- overview — Marco hands over keys ----

@router.get("/overview", response_class=HTMLResponse)
def overview(
    request: Request,
    note: str | None = None,
    error: str | None = None,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    return _render(request, "overview.html", {
        "rentals": rental_svc.list(),
        "cars": {c.car_id: c for c in car_svc.list()},
        "customers": {c.customer_id: c for c in customer_svc.list()},
        "note": note,
        "error": error,
        "active": "overview",
    })


@router.post("/overview/{rental_number}/handover")
def handover(rental_number: str, rental_svc: RentalService = Depends(get_rental_service)):
    try:
        _change_status(rental_svc, rental_number, "handed_over")
    except (ConflictError, NotFoundError) as exc:
        return _redirect("/overview", error=exc.message)
    return _redirect("/overview", note=f"{rental_number.upper()} handed over")


# ---- yard queue — Luca fetches cars ----

@router.get("/queue", response_class=HTMLResponse)
def yard_queue(
    request: Request,
    note: str | None = None,
    error: str | None = None,
    car_svc: CarService = Depends(get_car_service),
    customer_svc: CustomerService = Depends(get_customer_service),
    rental_svc: RentalService = Depends(get_rental_service),
):
    return _render(request, "yard_queue.html", {
        "rentals": rental_svc.list(status="requested"),
        "cars": {c.car_id: c for c in car_svc.list()},
        "customers": {c.customer_id: c for c in customer_svc.list()},
        "note": note,
        "error": error,
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
    except NotFoundError as exc:
        return _redirect("/queue", error=exc.message)
    return _render(request, "rental_detail.html", {
        "rental": rental,
        "car": car_svc.get(rental.car_id),
        "customer": customer_svc.get(rental.customer_id),
        "active": "queue",
    })


@router.post("/queue/{rental_number}/ready")
def mark_ready(rental_number: str, rental_svc: RentalService = Depends(get_rental_service)):
    try:
        _change_status(rental_svc, rental_number, "ready")
    except (ConflictError, NotFoundError) as exc:
        return _redirect("/queue", error=exc.message)
    return _redirect("/queue", note=f"{rental_number.upper()} marked ready")


# ---- new rental — Marco creates a rental ----

@router.get("/new-rental", response_class=HTMLResponse)
def new_rental_form(request: Request):
    return _render(request, "new_rental.html", {"active": "new-rental"})


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
    car_id: int | None = Form(None),
    rental_svc: RentalService = Depends(get_rental_service),
):
    ctx = {
        "active": "new-rental",
        "name": name,
        "licence_number": licence_number,
        "pickup_date": pickup_date,
        "return_date": return_date,
        "pickup_time": pickup_time,
        "category": category,
    }

    try:
        p = date.fromisoformat(pickup_date)
        r = date.fromisoformat(return_date)
    except ValueError:
        return _render(request, "new_rental.html", {**ctx, "error_dates": "Enter valid dates."})
    if r <= p:
        return _render(request, "new_rental.html", {
            **ctx, "error_dates": "Return date must be after pickup date."})
    if category not in CATEGORIES:
        return _render(request, "new_rental.html", {**ctx, "error": "Choose a car category."})

    def with_availability(extra: dict) -> HTMLResponse:
        availability = rental_svc.available(p, r, category)
        return _render(request, "new_rental.html", {
            **ctx, **extra,
            "available_cars": availability.cars,
            "other_categories": availability.other_categories,
        })

    if step != "create" or car_id is None:
        return with_availability({})

    try:
        booking = BookingIn(
            customer=CustomerIn(name=name, licence_number=licence_number),
            car_id=car_id, pickup_date=p, return_date=r, pickup_time=pickup_time,
        )
    except ValidationError as exc:
        return with_availability({"error": _validation_message(exc)})

    try:
        rental = rental_svc.book(booking)
    except (ConflictError, NotFoundError) as exc:
        # Usually the car was just booked by someone else: show fresh availability.
        return with_availability({"error": exc.message})

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
    return _render(request, "rental_created.html", {
        "rental": rental,
        "car": car_svc.get(rental.car_id),
        "customer": customer_svc.get(rental.customer_id),
        "active": "new-rental",
    })


# ---- customer status — Nina checks her rental ----

@router.get("/status", response_class=HTMLResponse)
def status_form(request: Request):
    return _render(request, "status.html", {})


@router.post("/status")
def status_post(rental_number: str = Form(...)):
    return RedirectResponse(f"/status/{quote(rental_number.strip().upper())}", status_code=303)


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
        return _render(request, "status.html", {
            "error": f"Rental number {rental_number} not found. Check your confirmation.",
            "rental_number": rental_number,
        })
    return _render(request, "status_result.html", {
        "rental": rental,
        "car": car_svc.get(rental.car_id),
    })
