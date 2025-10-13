"""Integration tests for the dashboard API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from klipperiwc.app import create_app

client = TestClient(create_app())


def _seed_status_history() -> None:
    response = client.get("/api/status")
    assert response.status_code == 200


def test_overview_endpoint_returns_payload() -> None:
    _seed_status_history()
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"updated_at", "state", "history"}
    assert payload["history"]["progress"]


def test_temperature_endpoint_returns_components() -> None:
    _seed_status_history()
    response = client.get("/api/dashboard/temperatures")
    assert response.status_code == 200
    payload = response.json()
    assert "components" in payload
    assert all("component" in entry for entry in payload["components"])


def test_job_endpoint_returns_recent_jobs() -> None:
    _seed_status_history()
    response = client.get("/api/dashboard/jobs")
    assert response.status_code == 200
    payload = response.json()
    assert "recent" in payload
    assert isinstance(payload["recent"], list)
