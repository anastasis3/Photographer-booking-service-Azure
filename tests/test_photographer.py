import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from PhotographerService.main import app, photographers

client = TestClient(app)

# =========================
# MOCK для Azure Queue
# =========================
class FakeQueue:
    def send_message(self, msg):
        pass

# =========================
# Happy path test (UPDATE)
# =========================
@patch("PhotographerService.main.QueueClient.from_connection_string")
def test_update_availability_happy_path(mock_queue_client):
    mock_queue_client.return_value = FakeQueue()

    photographer_id = 1
    payload = {"available": False}

    response = client.put(f"/photographers/{photographer_id}/availability", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Availability updated"
    assert data["photographer"]["id"] == photographer_id
    assert data["photographer"]["available"] is False

# =========================
# Bad scenario test (UPDATE)
# =========================
def test_update_availability_photographer_not_found():
    photographer_id = 99999
    payload = {"available": False}

    response = client.put(f"/photographers/{photographer_id}/availability", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Photographer not found"

# =========================
# NEW: Health check
# =========================
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "PhotographerService is running"}

# =========================
# NEW: Get all photographers
# =========================
def test_get_all_photographers():
    response = client.get("/photographers")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

# =========================
# NEW: Get photographer OK
# =========================
def test_get_photographer_ok():
    response = client.get("/photographers/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert "name" in data
    assert "available" in data
    assert "rating" in data

# =========================
# NEW: Get photographer NOT FOUND
# =========================
def test_get_photographer_not_found():
    response = client.get("/photographers/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Photographer not found"
