
import pytest
from unittest.mock import Mock, patch

from app import app, inventory


@pytest.fixture
def client():
    original_inventory = [item.copy() for item in inventory]
    inventory.clear()
    inventory.extend([
        {
            "id": 1,
            "barcode": "123456789",
            "product_name": "Test Milk",
            "brands": "Test Brand",
            "ingredients_text": "Milk",
            "quantity": 5,
            "price": 100.0
        }
    ])

    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    inventory.clear()
    inventory.extend(original_inventory)


def test_get_inventory(client):
    response = client.get("/inventory")

    assert response.status_code == 200
    assert response.json[0]["product_name"] == "Test Milk"


def test_get_one_item(client):
    response = client.get("/inventory/1")

    assert response.status_code == 200
    assert response.json["id"] == 1


def test_missing_item_returns_404(client):
    response = client.get("/inventory/999")

    assert response.status_code == 404


def test_add_item(client):
    response = client.post("/inventory", json={
        "product_name": "Bread",
        "quantity": 8,
        "price": 60
    })

    assert response.status_code == 201
    assert response.json["product_name"] == "Bread"
    assert response.json["id"] == 2


def test_add_item_rejects_invalid_quantity(client):
    response = client.post("/inventory", json={
        "product_name": "Bread",
        "quantity": -1,
        "price": 60
    })

    assert response.status_code == 400


def test_update_item(client):
    response = client.patch("/inventory/1", json={
        "price": 120,
        "quantity": 9
    })

    assert response.status_code == 200
    assert response.json["price"] == 120
    assert response.json["quantity"] == 9


def test_update_missing_item(client):
    response = client.patch("/inventory/999", json={"price": 50})

    assert response.status_code == 404


def test_delete_item(client):
    response = client.delete("/inventory/1")

    assert response.status_code == 200
    assert client.get("/inventory/1").status_code == 404


@patch("app.requests.get")
def test_external_barcode_lookup(mock_get, client):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "code": "3017620422003",
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "ingredients_text": "Water, almonds"
        }
    }
    mock_get.return_value = mock_response

    response = client.get("/inventory/lookup?barcode=3017620422003")

    assert response.status_code == 200
    assert response.json["product_name"] == "Organic Almond Milk"
    mock_get.assert_called_once()


@patch("app.requests.get")
def test_external_api_failure(mock_get, client):
    import requests

    mock_get.side_effect = requests.ConnectionError("Network unavailable")

    response = client.get("/inventory/lookup?barcode=123456789")

    assert response.status_code == 502
    assert "error" in response.json

@patch("app.requests.get")
def test_import_external_product(mock_get, client):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "code": "987654321",
            "product_name": "Almond Milk",
            "brands": "Test Brand",
            "ingredients_text": "Water, almonds"
        }
    }
    mock_get.return_value = mock_response

    response = client.post(
        "/inventory/import?barcode=987654321",
        json={"quantity": 5, "price": 150}
    )

    assert response.status_code == 201
    assert response.json["product_name"] == "Almond Milk"
    assert response.json["quantity"] == 5
    assert response.json["price"] == 150.0
    assert any(
        item["barcode"] == "987654321"
        for item in inventory
    )


@patch("app.requests.get")
def test_import_duplicate_product(mock_get, client):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "code": "123456789",
            "product_name": "Test Milk",
            "brands": "Test Brand",
            "ingredients_text": "Milk"
        }
    }
    mock_get.return_value = mock_response

    response = client.post(
        "/inventory/import?barcode=123456789",
        json={"quantity": 5, "price": 150}
    )

    assert response.status_code == 409
    assert "error" in response.json


@patch("app.requests.get")
def test_import_rejects_invalid_quantity(mock_get, client):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "code": "987654321",
            "product_name": "Almond Milk",
            "brands": "Test Brand",
            "ingredients_text": "Water, almonds"
        }
    }
    mock_get.return_value = mock_response

    response = client.post(
        "/inventory/import?barcode=987654321",
        json={"quantity": -1, "price": 150}
    )

    assert response.status_code == 400
    assert "error" in response.json


def test_import_requires_exactly_one_query(client):
    response = client.post("/inventory/import")

    assert response.status_code == 400
    assert "error" in response.json
