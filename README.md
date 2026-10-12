
# Inventory Management System

A Flask REST API and command-line interface for managing shop inventory.
The project uses a Python list as temporary storage and OpenFoodFacts
for external product lookups.

## Features

- View all inventory items and individual products.
- Add, update, and delete inventory items.
- Search OpenFoodFacts by barcode or product name.
- Validate user input and handle errors.
- Run automated tests with pytest.

## Requirements

- Python 3
- pip
- Internet connection for OpenFoodFacts lookups
- Git

## Installation

Clone the repository or open the project directory.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Start the API

```bash
python app.py
```

The API runs at http://127.0.0.1:5000.

## Start the CLI

Open another terminal in the project directory and activate the
virtual environment, then run:

```bash
python cli.py
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /inventory | List all items |
| GET | /inventory/1 | Get an item by ID |
| POST | /inventory | Add an item |
| PATCH | /inventory/1 | Update an item |
| DELETE | /inventory/1 | Delete an item |
| GET | /inventory/lookup?barcode=CODE | Search by barcode |
| GET | /inventory/lookup?name=Milk | Search by name |

### Add an item

Send a POST request to `/inventory` with JSON:

```json
{
  "product_name": "Milk",
  "barcode": "123456789",
  "quantity": 10,
  "price": 150
}
```

### Update an item

Send a PATCH request to `/inventory/1` with JSON:

```json
{
  "quantity": 15,
  "price": 175
}
```

## Run tests

```bash
pytest -v
```

## Storage

Inventory is held in an in-memory Python list. Changes are lost when
the Flask application restarts. This is simulated storage, not a
persistent database.

## External API

Product lookups use the OpenFoodFacts API. Network access is required for real lookups; automated tests mock the external API.

Products can also be imported from OpenFoodFacts into the inventory using the import endpoint. The endpoint validates the product information and rejects duplicate products or invalid input.

### Import a product

Send a POST request to `/inventory/import` with either a barcode or a product name.

Example using a barcode:

```bash
curl -X POST "http://127.0.0.1:5000/inventory/import?barcode=3017620422003"
```

Example using a product name:

```bash
curl -X POST "http://127.0.0.1:5000/inventory/import?name=Nutella"
```

A successful import adds the product to the in-memory inventory and returns a response with HTTP status `201 Created`. The API may return an error if the product cannot be found, the external service is unavailable, or the product already exists.

## License

Educational project.
