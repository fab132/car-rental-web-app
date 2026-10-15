NEW_CAR = {"make": "VW", "model": "Polo", "plate": "AG 999 001",
           "category": "compact", "parking_spot": "A01"}


def test_list_cars_returns_example_data(client):
    response = client.get("/cars")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_create_car_assigns_next_id(client):
    response = client.post("/cars", json=NEW_CAR)
    assert response.status_code == 201
    assert response.json()["car_id"] == 6
    assert client.get("/cars/6").json()["plate"] == "AG 999 001"


def test_create_car_with_unknown_category_is_422(client):
    response = client.post("/cars", json={**NEW_CAR, "category": "van"})
    assert response.status_code == 422


def test_create_car_with_unknown_field_is_422(client):
    response = client.post("/cars", json={**NEW_CAR, "available": True})
    assert response.status_code == 422


def test_duplicate_plate_is_409_regardless_of_case(client):
    response = client.post("/cars", json={**NEW_CAR, "plate": "ag 123 456"})
    assert response.status_code == 409


def test_get_unknown_car_is_404(client):
    assert client.get("/cars/99").status_code == 404


def test_update_car(client):
    response = client.put("/cars/3", json={**NEW_CAR, "plate": "AG 555 210", "parking_spot": "Z9"})
    assert response.status_code == 200
    assert client.get("/cars/3").json()["parking_spot"] == "Z9"


def test_delete_car_used_by_a_rental_is_409(client):
    assert client.delete("/cars/1").status_code == 409


def test_delete_free_car(client):
    car_id = client.post("/cars", json=NEW_CAR).json()["car_id"]
    assert client.delete(f"/cars/{car_id}").status_code == 204
    assert client.get(f"/cars/{car_id}").status_code == 404


def test_available_compact_falls_back_to_other_categories(client):
    # README example: on 24 to 27 September every compact car is rented,
    # so the free estate car is offered instead.
    response = client.get("/cars/available", params={
        "pickup_date": "2026-09-24", "return_date": "2026-09-27", "category": "compact"})
    body = response.json()
    assert response.status_code == 200
    assert body["other_categories"] is True
    assert [c["car_id"] for c in body["cars"]] == [3]


def test_available_with_reversed_dates_is_422(client):
    response = client.get("/cars/available", params={
        "pickup_date": "2026-09-27", "return_date": "2026-09-24"})
    assert response.status_code == 422
