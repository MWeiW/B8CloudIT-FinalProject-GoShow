import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "goshow_test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("NOTIFICATION_SERVICE_URL", "http://localhost:5999")
    monkeypatch.setenv("SERVERLESS_CONFIRMATION_URL", "http://localhost:5998/booking_confirmation")

    sys.modules.pop("app", None)
    sys.modules.pop("database", None)

    import app as app_module

    app_module.app.config.update(TESTING=True)
    app_module.init_database()

    monkeypatch.setattr(
        app_module,
        "send_booking_notification",
        lambda *args: {"status": "simulated"},
    )
    monkeypatch.setattr(
        app_module,
        "send_serverless_confirmation",
        lambda *args: {"status": "confirmed"},
    )

    with app_module.app.test_client() as test_client:
        yield test_client


def first_concert(client):
    response = client.get("/api/concerts")
    assert response.status_code == 200
    concerts = response.get_json()
    assert len(concerts) > 0
    return concerts[0]


def test_lists_concerts(client):
    concert = first_concert(client)
    assert "title" in concert
    assert "seats_available" in concert


def test_gets_single_concert(client):
    concert = first_concert(client)
    response = client.get(f"/api/concerts/{concert['id']}")
    assert response.status_code == 200
    assert response.get_json()["id"] == concert["id"]


def test_rejects_invalid_booking_values(client):
    concert = first_concert(client)
    response = client.post(
        "/api/bookings",
        json={
            "concert_id": concert["id"],
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "tickets": 0,
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_booking_updates_and_restores_seats(client):
    concert = first_concert(client)
    before_seats = concert["seats_available"]

    response = client.post(
        "/api/bookings",
        json={
            "concert_id": concert["id"],
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "tickets": 2,
        },
    )
    assert response.status_code == 201

    booking_id = response.get_json()["id"]
    updated = client.get(f"/api/concerts/{concert['id']}").get_json()
    assert updated["seats_available"] == before_seats - 2

    delete_response = client.delete(f"/api/bookings/{booking_id}")
    assert delete_response.status_code == 200

    restored = client.get(f"/api/concerts/{concert['id']}").get_json()
    assert restored["seats_available"] == before_seats


def test_rejects_invalid_concert_values(client):
    response = client.post(
        "/api/concerts",
        json={
            "title": "Test Show",
            "artist": "Test Artist",
            "venue": "Test Venue",
            "concert_date": "2026-09-01",
            "price": -5,
            "seats_available": 10,
            "description": "Small test concert.",
            "image_url": "https://example.com/test.jpg",
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_rejects_invalid_json(client):
    response = client.post(
        "/api/bookings",
        data="not json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
