
import requests

BASE_URL = "http://127.0.0.1:5000"


def show_inventory():
    response = requests.get(f"{BASE_URL}/inventory", timeout=10)
    response.raise_for_status()
    items = response.json()

    if not items:
        print("Inventory is empty.")
        return

    for item in items:
        print(
            f'ID: {item["id"]} | {item["product_name"]} | '
            f'Quantity: {item["quantity"]} | Price: {item["price"]}'
        )


def add_inventory_item():
    product_name = input("Product name: ").strip()
    barcode = input("Barcode (optional): ").strip()

    try:
        quantity = int(input("Quantity: "))
        price = float(input("Price: "))

        if quantity < 0 or price < 0:
            print("Quantity and price cannot be negative.")
            return

        payload = {
            "product_name": product_name,
            "barcode": barcode,
            "quantity": quantity,
            "price": price
        }

        response = requests.post(
            f"{BASE_URL}/inventory",
            json=payload,
            timeout=10
        )
        print(response.status_code, response.json())

    except ValueError:
        print("Please enter a valid number for quantity and price.")
    except requests.RequestException as error:
        print(f"Could not reach the Flask API: {error}")


def view_item():
    try:
        item_id = int(input("Enter product ID: "))
        response = requests.get(
            f"{BASE_URL}/inventory/{item_id}",
            timeout=10
        )
        print(response.status_code, response.json())
    except ValueError:
        print("Product ID must be a number.")
    except requests.RequestException as error:
        print(f"Could not reach the Flask API: {error}")


def update_inventory_item():
    try:
        item_id = int(input("Enter product ID to update: "))
        print("Leave a field blank to keep its current value.")

        name = input("New product name: ").strip()
        quantity_text = input("New quantity: ").strip()
        price_text = input("New price: ").strip()

        payload = {}

        if name:
            payload["product_name"] = name
        if quantity_text:
            payload["quantity"] = int(quantity_text)
        if price_text:
            payload["price"] = float(price_text)

        if not payload:
            print("No changes entered.")
            return

        response = requests.patch(
            f"{BASE_URL}/inventory/{item_id}",
            json=payload,
            timeout=10
        )
        print(response.status_code, response.json())

    except ValueError:
        print("Enter a valid ID, quantity, and price.")
    except requests.RequestException as error:
        print(f"Could not reach the Flask API: {error}")


def delete_inventory_item():
    try:
        item_id = int(input("Enter product ID to delete: "))
        response = requests.delete(
            f"{BASE_URL}/inventory/{item_id}",
            timeout=10
        )
        print(response.status_code, response.json())
    except ValueError:
        print("Product ID must be a number.")
    except requests.RequestException as error:
        print(f"Could not reach the Flask API: {error}")


def lookup_external_product():
    query_type = input("Search by barcode or name? ").strip().lower()

    if query_type == "barcode":
        query = input("Enter barcode: ").strip()
        params = {"barcode": query}
    elif query_type == "name":
        query = input("Enter product name: ").strip()
        params = {"name": query}
    else:
        print("Choose barcode or name.")
        return

    if not query:
        print("Your search cannot be empty.")
        return

    try:
        response = requests.get(
            f"{BASE_URL}/inventory/lookup",
            params=params,
            timeout=15
        )
        print(response.status_code, response.json())

        # The user can use these returned details to add the product.
        if response.ok:
            print("Use the returned product details when adding an inventory item.")
    except requests.RequestException as error:
        print(f"Could not reach the Flask API: {error}")


def main():
    actions = {
        "1": ("View all inventory", show_inventory),
        "2": ("View one product", view_item),
        "3": ("Add a product", add_inventory_item),
        "4": ("Update a product", update_inventory_item),
        "5": ("Delete a product", delete_inventory_item),
        "6": ("Search OpenFoodFacts", lookup_external_product)
    }

    while True:
        print("\n=== INVENTORY MANAGEMENT ===")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("0. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Select an option from 0 to 6.")
            continue

        try:
            action[1]()
        except requests.RequestException as error:
            print(f"Request failed: {error}")
        except (ValueError, TypeError) as error:
            print(f"Invalid data: {error}")


if __name__ == "__main__":
    main()
