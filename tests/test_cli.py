
from unittest.mock import Mock, patch

import cli


@patch("cli.requests.get")
def test_show_inventory(mock_get, capsys):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "id": 1,
            "product_name": "Milk",
            "quantity": 5,
            "price": 100
        }
    ]
    mock_get.return_value = mock_response

    cli.show_inventory()

    output = capsys.readouterr().out
    assert "Milk" in output
    assert "Quantity: 5" in output


@patch("builtins.input", side_effect=["invalid", "0"])
def test_cli_handles_invalid_menu_choice(mock_input, capsys):
    cli.main()

    output = capsys.readouterr().out
    assert "Invalid choice" in output
    assert "Goodbye" in output


@patch("cli.requests.post")
@patch("builtins.input", side_effect=["Bread", "12345", "5", "60"])
def test_add_inventory_item(mock_input, mock_post, capsys):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 3,
        "product_name": "Bread",
        "quantity": 5,
        "price": 60
    }
    mock_post.return_value = mock_response

    cli.add_inventory_item()

    assert mock_post.called
    assert mock_post.call_args.kwargs["json"]["product_name"] == "Bread"
