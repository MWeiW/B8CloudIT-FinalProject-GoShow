import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIR = ROOT / "notification_service"
sys.path.insert(0, str(SERVICE_DIR))

import service as service_module


def test_notification_health():
    with service_module.app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "notification-service",
    }


def test_notification_is_reported_as_simulated():
    with service_module.app.test_client() as client:
        response = client.post(
            "/notify",
            json={
                "customer_name": "Test User",
                "customer_email": "test@example.com",
                "concert_title": "Test Concert",
                "tickets": 2,
            },
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "simulated"
    assert data["recipient"] == "test@example.com"
    assert "Test Concert" in data["message"]
    assert "2 ticket(s)" in data["message"]


def test_notification_rejects_invalid_json():
    with service_module.app.test_client() as client:
        response = client.post(
            "/notify",
            data="not json",
            content_type="application/json",
        )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid JSON request"
