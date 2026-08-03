import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUNCTION_DIR = ROOT / "serverless" / "booking_confirmation"
sys.path.insert(0, str(FUNCTION_DIR))

import handler


def response_body(event):
    result = handler.handle(event)
    assert result["statusCode"] == 200
    return json.loads(result["body"])


def test_serverless_confirmation_uses_generic_defaults():
    data = response_body({})

    assert data["status"] == "confirmed"
    assert data["customer_name"] == "Customer"
    assert data["customer_email"] == "not-provided@example.com"
    assert data["concert_title"] == "your selected concert"
    assert data["tickets"] == 1
    assert data["confirmation_id"].startswith("GOSHOW-")
    datetime.fromisoformat(data["confirmed_at"])


def test_serverless_confirmation_uses_booking_data():
    data = response_body(
        {
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "concert_title": "Test Concert",
            "tickets": 3,
        }
    )

    assert data["customer_name"] == "Test User"
    assert data["customer_email"] == "test@example.com"
    assert data["concert_title"] == "Test Concert"
    assert data["tickets"] == 3
    assert "3 ticket(s)" in data["message"]
