from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

inventory = [
    {
        "id": 1,
        "barcode": "3017620422003",
        "product_name": "Nutella",
        "brands": "Ferrero",
        "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa",
        "quantity": 10,
        "price": 450.0
    },
    {
        "id": 2,
        "barcode": "5449000000996",
        "product_name": "Coca-Cola",
        "brands": "Coca-Cola",
        "ingredients_text": "Carbonated water, sugar, caramel colour",
        "quantity": 20,
        "price": 150.0
    }
]


def next_id():
    return max((item["id"] for item in inventory), default=0) + 1


def fetch_external_product(barcode=None, name=None):
    headers = {
        "User-Agent": "InventoryManagementSystem/1.0 (student project)"
    }

    fields = "product_name,brands,ingredients_text,code"

    try:
        if barcode:
            url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
            response = requests.get(
                url,
                params={"fields": fields},
                headers=headers,
                timeout=20
            )
        elif name:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            response = requests.get(
                url,
                params={
                    "search_terms": name,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": 1,
                    "fields": fields
                },
                headers=headers,
                timeout=20
            )
        else:
            return None, "Provide a barcode or product name."

        response.raise_for_status()
        data = response.json()

        if barcode:
            if data.get("status") != 1 or not data.get("product"):
                return None, "Product not found in OpenFoodFacts."
            product = data["product"]
        else:
            results = data.get("products", [])
            if not results:
                return None, "Product not found in OpenFoodFacts."
            product = results[0]

        product_name = product.get("product_name", "").strip()
        if not product_name:
            return None, "Product has no name in OpenFoodFacts."

        return {
            "barcode": str(product.get("code") or barcode or ""),
            "product_name": product_name,
            "brands": product.get("brands", ""),
            "ingredients_text": product.get("ingredients_text", "")
        }, None

    except requests.RequestException as error:
        app.logger.warning("OpenFoodFacts request failed: %s", error)
        return None, "Could not connect to OpenFoodFacts."
    except (ValueError, TypeError) as error:
        app.logger.warning("Invalid OpenFoodFacts response: %s", error)
        return None, "OpenFoodFacts returned an invalid response."


def find_item(item_id):
    return next(
        (item for item in inventory if item["id"] == item_id),
        None
    )


def validate_quantity(quantity):
    return (
        isinstance(quantity, int)
        and not isinstance(quantity, bool)
        and quantity >= 0
    )


def validate_price(price):
    return (
        isinstance(price, (int, float))
        and not isinstance(price, bool)
        and price >= 0
    )


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to the Inventory Management API",
        "endpoints": [
            "GET /inventory",
            "GET /inventory/<id>",
            "POST /inventory",
            "PATCH /inventory/<id>",
            "DELETE /inventory/<id>",
            "GET /inventory/lookup?barcode=<barcode>",
            "GET /inventory/lookup?name=<name>",
            "POST /inventory/import?barcode=<barcode>",
            "POST /inventory/import?name=<name>"
        ]
    }), 200


@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)

    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404

    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def add_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    product_name = data.get("product_name", data.get("name"))
    quantity = data.get("quantity")
    price = data.get("price")

    if not isinstance(product_name, str) or not product_name.strip():
        return jsonify({"error": "product_name is required"}), 400

    if not validate_quantity(quantity):
        return jsonify({"error": "quantity must be a non-negative integer"}), 400

    if not validate_price(price):
        return jsonify({"error": "price must be a non-negative number"}), 400

    barcode = data.get("barcode", "")
    brands = data.get("brands", "")
    ingredients_text = data.get("ingredients_text", "")

    if not all(isinstance(value, str) for value in
               (barcode, brands, ingredients_text)):
        return jsonify({
            "error": "barcode, brands, and ingredients_text must be strings"
        }), 400

    barcode = barcode.strip()

    if barcode and any(item["barcode"] == barcode for item in inventory):
        return jsonify({"error": "An item with this barcode already exists"}), 409

    item = {
        "id": next_id(),
        "barcode": barcode,
        "product_name": product_name.strip(),
        "brands": brands.strip(),
        "ingredients_text": ingredients_text.strip(),
        "quantity": quantity,
        "price": float(price)
    }

    inventory.append(item)
    return jsonify(item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)

    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Provide a non-empty JSON object"}), 400

    allowed_fields = {
        "barcode", "product_name", "brands",
        "ingredients_text", "quantity", "price"
    }

    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        return jsonify({
            "error": "Unknown fields",
            "fields": sorted(unknown_fields)
        }), 400

    if "product_name" in data:
        if not isinstance(data["product_name"], str) or not data["product_name"].strip():
            return jsonify({"error": "product_name cannot be empty"}), 400

    if "quantity" in data and not validate_quantity(data["quantity"]):
        return jsonify({"error": "quantity must be a non-negative integer"}), 400

    if "price" in data and not validate_price(data["price"]):
        return jsonify({"error": "price must be a non-negative number"}), 400

    for field in ("barcode", "brands", "ingredients_text"):
        if field in data and not isinstance(data[field], str):
            return jsonify({"error": f"{field} must be a string"}), 400

    new_barcode = data.get("barcode", item["barcode"])
    if isinstance(new_barcode, str):
        new_barcode = new_barcode.strip()

    if new_barcode and any(
        other["id"] != item_id and other["barcode"] == new_barcode
        for other in inventory
    ):
        return jsonify({"error": "An item with this barcode already exists"}), 409

    for field, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        item[field] = value

    if "price" in data:
        item["price"] = float(data["price"])

    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)

    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404

    inventory.remove(item)
    return jsonify({"message": "Inventory item deleted successfully"}), 200


@app.route("/inventory/lookup", methods=["GET"])
def lookup_product():
    barcode = request.args.get("barcode", "").strip()
    name = request.args.get("name", "").strip()

    if bool(barcode) == bool(name):
        return jsonify({
            "error": "Provide exactly one query: barcode or name"
        }), 400

    product, error = fetch_external_product(
        barcode=barcode or None,
        name=name or None
    )

    if error:
        if error.startswith("Could not connect") or error.startswith("OpenFoodFacts returned"):
            return jsonify({"error": error}), 502
        return jsonify({"error": error}), 404

    return jsonify(product), 200


@app.route("/inventory/import", methods=["POST"])
def import_product():
    barcode = request.args.get("barcode", "").strip()
    name = request.args.get("name", "").strip()

    if bool(barcode) == bool(name):
        return jsonify({
            "error": "Provide exactly one query: barcode or name"
        }), 400

    product, error = fetch_external_product(
        barcode=barcode or None,
        name=name or None
    )

    if error:
        if error.startswith("Could not connect") or error.startswith("OpenFoodFacts returned"):
            return jsonify({"error": error}), 502
        return jsonify({"error": error}), 404

    if not product["barcode"]:
        return jsonify({
            "error": "Product has no barcode and cannot be imported"
        }), 400

    existing = next(
        (item for item in inventory if item["barcode"] == product["barcode"]),
        None
    )

    if existing:
        return jsonify({
            "error": "Product already exists in inventory",
            "item": existing
        }), 409

    data = request.get_json(silent=True)
    if data is None:
        data = {}

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    quantity = data.get("quantity", 0)
    price = data.get("price", 0)

    if not validate_quantity(quantity):
        return jsonify({"error": "quantity must be a non-negative integer"}), 400

    if not validate_price(price):
        return jsonify({"error": "price must be a non-negative number"}), 400

    item = {
        "id": next_id(),
        **product,
        "quantity": quantity,
        "price": float(price)
    }

    inventory.append(item)
    return jsonify(item), 201


if __name__ == "__main__":
    app.run(debug=True)
