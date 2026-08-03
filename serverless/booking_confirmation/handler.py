import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DEFAULT_BOOKING = {
    "customer_name": "Customer",
    "customer_email": "not-provided@example.com",
    "concert_title": "your selected concert",
    "tickets": 1,
}


def _parse_event(event):
    if isinstance(event, str):
        return json.loads(event)
    if isinstance(event, dict):
        body = event.get("body")
        if isinstance(body, str):
            return json.loads(body)
        if isinstance(body, dict):
            return body
        return event
    return {}


def handle(event, context=None):
    booking = {**DEFAULT_BOOKING, **_parse_event(event)}

    try:
        tickets = int(booking.get("tickets", DEFAULT_BOOKING["tickets"]))
    except (TypeError, ValueError):
        tickets = DEFAULT_BOOKING["tickets"]

    response_body = {
        "status": "confirmed",
        "confirmation_id": f"GOSHOW-{uuid4().hex[:10].upper()}",
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "customer_name": booking.get("customer_name") or DEFAULT_BOOKING["customer_name"],
        "customer_email": booking.get("customer_email") or DEFAULT_BOOKING["customer_email"],
        "concert_title": booking.get("concert_title") or DEFAULT_BOOKING["concert_title"],
        "tickets": tickets,
        "message": (
            f"Booking confirmed for {tickets} ticket(s) to "
            f"{booking.get('concert_title') or DEFAULT_BOOKING['concert_title']}."
        ),
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response_body),
    }


if __name__ == "__main__":
    sample_path = Path(__file__).with_name("sample_event.json")
    sample_event = json.loads(sample_path.read_text())
    print(json.dumps(handle(sample_event), indent=2))
