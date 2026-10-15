from datetime import date

from app.services import periods_overlap


def test_yard_queue_lists_requested_rentals_by_pickup(client):
    response = client.get("/rentals", params={"status": "requested"})
    assert [r["rental_number"] for r in response.json()] == ["R-105"]


def test_get_rental_is_case_insensitive(client):
    assert client.get("/rentals/r-104").json()["rental_number"] == "R-104"


def test_get_unknown_rental_is_404(client):
    assert client.get("/rentals/R-999").status_code == 404


def test_create_rental_starts_as_requested_with_next_number(client, rental_body):
    response = client.post("/rentals", json=rental_body)
    assert response.status_code == 201
    assert response.json()["status"] == "requested"
    assert response.json()["rental_number"] == "R-106"


def test_create_rental_cannot_set_status(client, rental_body):
    response = client.post("/rentals", json={**rental_body, "status": "ready"})
    assert response.status_code == 422


def test_return_before_pickup_is_422(client, rental_body):
    response = client.post("/rentals", json={**rental_body, "return_date": "2026-09-23"})
    assert response.status_code == 422


def test_bad_pickup_time_is_422(client, rental_body):
    response = client.post("/rentals", json={**rental_body, "pickup_time": "25:00"})
    assert response.status_code == 422


def test_unknown_car_is_404(client, rental_body):
    assert client.post("/rentals", json={**rental_body, "car_id": 99}).status_code == 404


def test_unknown_customer_is_404(client, rental_body):
    assert client.post("/rentals", json={**rental_body, "customer_id": 99}).status_code == 404


def test_overlapping_rental_for_same_car_is_409(client, rental_body):
    # Car 1 is rented as R-104 from 24 to 27 September.
    response = client.post("/rentals", json={**rental_body, "car_id": 1,
                                             "pickup_date": "2026-09-25",
                                             "return_date": "2026-09-26"})
    assert response.status_code == 409
    assert "R-104" in response.json()["detail"]


def test_pickup_on_return_day_is_allowed(client, rental_body):
    response = client.post("/rentals", json={**rental_body, "car_id": 1,
                                             "pickup_date": "2026-09-27",
                                             "return_date": "2026-09-29"})
    assert response.status_code == 201


def test_requested_to_ready_to_handed_over(client, rental_body):
    number = client.post("/rentals", json=rental_body).json()["rental_number"]
    assert client.put(f"/rentals/{number}", json={**rental_body, "status": "ready"}).status_code == 200
    response = client.put(f"/rentals/{number}", json={**rental_body, "status": "handed_over"})
    assert response.status_code == 200
    assert response.json()["status"] == "handed_over"


def test_requested_cannot_jump_to_handed_over(client, rental_body):
    # Business rule 6: only a ready rental can be handed over.
    number = client.post("/rentals", json=rental_body).json()["rental_number"]
    response = client.put(f"/rentals/{number}", json={**rental_body, "status": "handed_over"})
    assert response.status_code == 409


def test_handed_over_rental_cannot_change(client):
    body = {"customer_id": 3, "car_id": 4, "pickup_date": "2026-09-24",
            "return_date": "2026-09-26", "pickup_time": "08:00", "status": "handed_over"}
    assert client.put("/rentals/R-101", json=body).status_code == 409


def test_update_keeps_own_period_free(client):
    # Moving R-104 by its own pickup time must not clash with itself.
    body = {"customer_id": 1, "car_id": 1, "pickup_date": "2026-09-24",
            "return_date": "2026-09-27", "pickup_time": "09:30", "status": "ready"}
    assert client.put("/rentals/R-104", json=body).status_code == 200


def test_delete_rental_frees_the_car(client, rental_body):
    assert client.delete("/rentals/R-104").status_code == 204
    response = client.post("/rentals", json={**rental_body, "car_id": 1})
    assert response.status_code == 201


def test_periods_overlap_rule():
    d = date.fromisoformat
    assert periods_overlap(d("2026-09-24"), d("2026-09-27"), d("2026-09-26"), d("2026-09-28"))
    assert not periods_overlap(d("2026-09-24"), d("2026-09-27"), d("2026-09-27"), d("2026-09-28"))
