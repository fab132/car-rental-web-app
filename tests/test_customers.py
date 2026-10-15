NEW_CUSTOMER = {"name": "Lea Brunner", "licence_number": "CH 5550001"}


def test_list_customers(client):
    assert len(client.get("/customers").json()) == 4


def test_create_customer(client):
    response = client.post("/customers", json=NEW_CUSTOMER)
    assert response.status_code == 201
    assert response.json()["customer_id"] == 5


def test_missing_licence_is_422(client):
    # Business rule 1: no customer without a licence number.
    response = client.post("/customers", json={"name": "Lea Brunner"})
    assert response.status_code == 422


def test_blank_name_is_422(client):
    response = client.post("/customers", json={**NEW_CUSTOMER, "name": "   "})
    assert response.status_code == 422


def test_duplicate_licence_is_409(client):
    response = client.post("/customers", json={"name": "Someone", "licence_number": "CH 1234567"})
    assert response.status_code == 409


def test_update_unknown_customer_is_404(client):
    assert client.put("/customers/99", json=NEW_CUSTOMER).status_code == 404


def test_delete_customer_with_rentals_is_409(client):
    assert client.delete("/customers/1").status_code == 409


def test_delete_customer_without_rentals(client):
    customer_id = client.post("/customers", json=NEW_CUSTOMER).json()["customer_id"]
    assert client.delete(f"/customers/{customer_id}").status_code == 204
