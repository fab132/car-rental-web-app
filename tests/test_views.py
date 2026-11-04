"""Workflow screens: each page renders, and failed actions show a message
on the page instead of a 500 or the API's JSON error body."""

import pytest

NEW_RENTAL = {
    "name": "Lea Brunner",
    "licence_number": "CH 3141592",
    "pickup_date": "2026-12-01",
    "return_date": "2026-12-03",
    "pickup_time": "09:00",
    "category": "estate",
}


@pytest.mark.parametrize("path", ["/", "/overview", "/queue", "/queue/R-105",
                                  "/new-rental", "/status", "/status/R-104"])
def test_screens_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_html_routes_are_not_in_the_api_contract(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert not [p for p in paths if p.startswith(("/overview", "/queue", "/new-rental", "/status"))]
    assert "/" not in paths


# ---- yard queue and overview ----

def test_mark_ready_moves_rental_out_of_the_queue(client):
    response = client.post("/queue/R-105/ready")
    assert response.status_code == 200
    assert "R-105 marked ready" in response.text
    assert client.get("/rentals/R-105").json()["status"] == "ready"


def test_mark_ready_on_handed_over_rental_shows_error(client):
    response = client.post("/queue/R-103/ready")
    assert response.status_code == 200
    assert "handed over and cannot change" in response.text
    assert client.get("/rentals/R-103").json()["status"] == "handed_over"


def test_queue_detail_of_handed_over_rental_has_no_mark_ready(client):
    response = client.get("/queue/R-103")
    assert "Mark ready" not in response.text
    assert "Handed over" in response.text


def test_unknown_queue_rental_shows_error(client):
    response = client.get("/queue/R-999")
    assert response.status_code == 200
    assert "Rental R-999 not found" in response.text


def test_hand_over_ready_rental(client):
    response = client.post("/overview/R-104/handover")
    assert "R-104 handed over" in response.text
    assert client.get("/rentals/R-104").json()["status"] == "handed_over"


def test_hand_over_requested_rental_shows_error(client):
    response = client.post("/overview/R-105/handover")
    assert response.status_code == 200
    assert "Status cannot change from requested to handed_over" in response.text
    assert client.get("/rentals/R-105").json()["status"] == "requested"


# ---- new rental ----

def test_search_lists_free_cars_in_category(client):
    response = client.post("/new-rental", data=NEW_RENTAL)
    assert "Octavia" in response.text
    assert "Golf" not in response.text


def test_create_rental_for_new_customer(client):
    response = client.post("/new-rental", data={**NEW_RENTAL, "step": "create", "car_id": "3"})
    assert response.status_code == 200
    assert "R-106 created for Lea Brunner" in response.text
    customers = client.get("/customers").json()
    assert [c["name"] for c in customers].count("Lea Brunner") == 1


def test_returning_customer_is_reused(client):
    data = {**NEW_RENTAL, "name": "Nina Keller", "licence_number": "ch 1234567",
            "step": "create", "car_id": "3"}
    client.post("/new-rental", data=data)
    assert len(client.get("/customers").json()) == 4
    assert client.get("/rentals/R-106").json()["customer_id"] == 1


def test_conflicting_booking_shows_error_and_stores_nothing(client):
    # Car 1 is rented as R-104 from 24 to 27 September.
    data = {**NEW_RENTAL, "pickup_date": "2026-09-25", "return_date": "2026-09-26",
            "category": "compact", "step": "create", "car_id": "1"}
    response = client.post("/new-rental", data=data)
    assert response.status_code == 200
    assert "already rented in this period" in response.text
    assert len(client.get("/customers").json()) == 4
    assert len(client.get("/rentals").json()) == 4


@pytest.mark.parametrize("field, value, message", [
    ("licence_number", "AB", "Licence number: String should have at least 3 characters"),
    ("pickup_time", "9am", "Pickup time: use the format HH:MM"),
])
def test_invalid_input_shows_form_error(client, field, value, message):
    data = {**NEW_RENTAL, field: value, "step": "create", "car_id": "3"}
    response = client.post("/new-rental", data=data)
    assert response.status_code == 200
    assert message in response.text
    assert len(client.get("/rentals").json()) == 4


def test_return_before_pickup_shows_form_error(client):
    response = client.post("/new-rental", data={**NEW_RENTAL, "return_date": "2026-11-30"})
    assert "Return date must be after pickup date." in response.text


def test_unknown_category_shows_form_error(client):
    response = client.post("/new-rental", data={**NEW_RENTAL, "category": "bus"})
    assert response.status_code == 200
    assert "Choose a car category." in response.text


# ---- customer status ----

def test_status_lookup_redirects_to_result(client):
    response = client.post("/status", data={"rental_number": " r-104 "})
    assert response.url.path == "/status/R-104"
    assert "Your car is waiting at the pickup area" in response.text


def test_unknown_status_shows_error(client):
    response = client.get("/status/R-999")
    assert response.status_code == 200
    assert "Rental number R-999 not found" in response.text
