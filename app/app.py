import os
import re
from datetime import date, datetime
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, render_template, request

from database import get_connection, init_database, row_to_dict


app = Flask(__name__)
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5001")
SERVERLESS_CONFIRMATION_URL = os.environ.get(
    "SERVERLESS_CONFIRMATION_URL",
    "https://goshow-booking-confirmation-wingwei8.azurewebsites.net/api/booking_confirmation",
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONCERT_FIELDS = ["title", "artist", "venue", "concert_date", "price", "seats_available", "description", "image_url"]
MAX_TICKETS_PER_BOOKING = 10


def json_error(message, status=400):
    return jsonify({"error": message}), status


def read_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, json_error("Invalid JSON request")
    return data, None


def text_value(data, field, limit):
    value = str(data.get(field, "")).strip()
    if not value:
        raise ValueError(f"{field.replace('_', ' ')} is required")
    if len(value) > limit:
        raise ValueError(f"{field.replace('_', ' ')} is too long")
    return value


def whole_number(value, label, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number")

    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{label} must be at most {maximum}")
    return number


def money_value(value, label, minimum=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number")

    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must not be negative")
    return number


def concert_date_value(value):
    value = str(value).strip()
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("concert date must use YYYY-MM-DD")

    if parsed_date < date.today():
        raise ValueError("concert date must not be in the past")
    return value


def image_url_value(value):
    value = str(value).strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image url must be a valid http or https URL")
    return value


def validate_concert_payload(data):
    if any(field not in data for field in CONCERT_FIELDS):
        raise ValueError("Missing concert fields")

    return {
        "title": text_value(data, "title", 120),
        "artist": text_value(data, "artist", 120),
        "venue": text_value(data, "venue", 160),
        "concert_date": concert_date_value(data["concert_date"]),
        "price": money_value(data["price"], "price", minimum=0),
        "seats_available": whole_number(data["seats_available"], "seats available", minimum=0),
        "description": text_value(data, "description", 800),
        "image_url": image_url_value(data["image_url"]),
    }


def validate_booking_payload(data):
    required = ["concert_id", "customer_name", "customer_email", "tickets"]
    if any(field not in data for field in required):
        raise ValueError("Missing booking fields")

    customer_name = text_value(data, "customer_name", 100)
    customer_email = text_value(data, "customer_email", 160)

    if not EMAIL_PATTERN.match(customer_email):
        raise ValueError("customer email is not valid")

    return {
        "concert_id": whole_number(data["concert_id"], "concert id", minimum=1),
        "customer_name": customer_name,
        "customer_email": customer_email,
        "tickets": whole_number(data["tickets"], "tickets", minimum=1, maximum=MAX_TICKETS_PER_BOOKING),
    }


@app.route("/")
def home_page():
    return render_template("home.html")


@app.route("/concerts")
def concerts_page():
    return render_template("concerts.html")


@app.route("/about")
def about_page():
    return render_template("about.html")


@app.route("/concerts/<int:concert_id>")
def concert_details_page(concert_id):
    return render_template("details.html", concert_id=concert_id)


@app.route("/bookings")
def bookings_page():
    return render_template("bookings.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "goshow-app"})


@app.route("/api/concerts", methods=["GET"])
def get_concerts():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM concerts ORDER BY concert_date").fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/concerts/<int:concert_id>", methods=["GET"])
def get_concert(concert_id):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM concerts WHERE id = ?", (concert_id,)).fetchone()
    concert = row_to_dict(row)
    if not concert:
        return json_error("Concert not found", 404)
    return jsonify(concert)


@app.route("/api/concerts", methods=["POST"])
def add_concert():
    data, error = read_json_body()
    if error:
        return error

    try:
        concert = validate_concert_payload(data)
    except ValueError as error:
        return json_error(str(error))

    with get_connection() as connection:
        concert_id = connection.insert_and_get_id(
            """
            INSERT INTO concerts
            (title, artist, venue, concert_date, price, seats_available, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concert["title"],
                concert["artist"],
                concert["venue"],
                concert["concert_date"],
                concert["price"],
                concert["seats_available"],
                concert["description"],
                concert["image_url"],
            ),
        )
        connection.commit()

    return jsonify({"message": "Concert added", "id": concert_id}), 201


@app.route("/api/concerts/<int:concert_id>", methods=["PUT"])
def update_concert(concert_id):
    data, error = read_json_body()
    if error:
        return error

    try:
        concert = validate_concert_payload(data)
    except ValueError as error:
        return json_error(str(error))

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE concerts
            SET title = ?, artist = ?, venue = ?, concert_date = ?, price = ?,
                seats_available = ?, description = ?, image_url = ?
            WHERE id = ?
            """,
            (
                concert["title"],
                concert["artist"],
                concert["venue"],
                concert["concert_date"],
                concert["price"],
                concert["seats_available"],
                concert["description"],
                concert["image_url"],
                concert_id,
            ),
        )
        connection.commit()
        updated = cursor.rowcount

    if updated == 0:
        return json_error("Concert not found", 404)
    return jsonify({"message": "Concert updated"})


@app.route("/api/concerts/<int:concert_id>", methods=["DELETE"])
def delete_concert(concert_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM bookings WHERE concert_id = ?", (concert_id,))
        cursor = connection.execute("DELETE FROM concerts WHERE id = ?", (concert_id,))
        connection.commit()
        deleted = cursor.rowcount

    if deleted == 0:
        return json_error("Concert not found", 404)
    return jsonify({"message": "Concert deleted"})


@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT bookings.*, concerts.title, concerts.artist, concerts.venue, concerts.concert_date
            FROM bookings
            JOIN concerts ON bookings.concert_id = concerts.id
            ORDER BY bookings.created_at DESC
            """
        ).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data, error = read_json_body()
    if error:
        return error

    try:
        booking = validate_booking_payload(data)
    except ValueError as error:
        return json_error(str(error))

    with get_connection() as connection:
        concert = connection.execute(
            "SELECT * FROM concerts WHERE id = ?",
            (booking["concert_id"],),
        ).fetchone()

        if not concert:
            return json_error("Concert not found", 404)

        update_cursor = connection.execute(
            """
            UPDATE concerts
            SET seats_available = seats_available - ?
            WHERE id = ? AND seats_available >= ?
            """,
            (booking["tickets"], booking["concert_id"], booking["tickets"]),
        )

        if update_cursor.rowcount == 0:
            connection.rollback()
            return json_error("Not enough seats available")

        booking_id = connection.insert_and_get_id(
            """
            INSERT INTO bookings (concert_id, customer_name, customer_email, tickets)
            VALUES (?, ?, ?, ?)
            """,
            (
                booking["concert_id"],
                booking["customer_name"],
                booking["customer_email"],
                booking["tickets"],
            ),
        )
        connection.commit()
        concert_title = concert["title"]

    notification = send_booking_notification(
        booking["customer_name"],
        booking["customer_email"],
        concert_title,
        booking["tickets"],
    )
    serverless_confirmation = send_serverless_confirmation(
        booking["customer_name"],
        booking["customer_email"],
        concert_title,
        booking["tickets"],
    )

    return jsonify(
        {
            "message": "Booking created",
            "id": booking_id,
            "notification": notification,
            "serverless_confirmation": serverless_confirmation,
        }
    ), 201


@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    with get_connection() as connection:
        booking = connection.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if not booking:
            return json_error("Booking not found", 404)

        connection.execute(
            "UPDATE concerts SET seats_available = seats_available + ? WHERE id = ?",
            (booking["tickets"], booking["concert_id"]),
        )
        connection.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        connection.commit()

    return jsonify({"message": "Booking cancelled"})


def post_service_json(url, payload, timeout, fallback_message):
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except ValueError:
        return {"status": "skipped", "message": "Invalid service response"}
    except requests.RequestException:
        return {"status": "skipped", "message": fallback_message}


def send_booking_notification(customer_name, customer_email, concert_title, tickets):
    return post_service_json(
        f"{NOTIFICATION_SERVICE_URL}/notify",
        {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "concert_title": concert_title,
            "tickets": tickets,
        },
        2,
        "Notification service unavailable",
    )


def send_serverless_confirmation(customer_name, customer_email, concert_title, tickets):
    return post_service_json(
        SERVERLESS_CONFIRMATION_URL,
        {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "concert_title": concert_title,
            "tickets": tickets,
        },
        3,
        "Serverless confirmation unavailable",
    )


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5000, debug=False)
