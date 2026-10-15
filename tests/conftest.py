"""Every test gets a fresh copy of the example data in a temporary folder,
so tests never touch data/store/ and never depend on each other."""

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_data_dir
from app.main import app


@pytest.fixture
def client(tmp_path):
    app.dependency_overrides[get_data_dir] = lambda: tmp_path
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def rental_body():
    # Tom Meier rents the estate car, which is free on these dates in the example data.
    return {
        "customer_id": 2,
        "car_id": 3,
        "pickup_date": "2026-09-24",
        "return_date": "2026-09-27",
        "pickup_time": "11:00",
    }
