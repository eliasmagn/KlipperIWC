"""Tests for the status API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from klipperiwc.app import create_app

client = TestClient(create_app())


def test_status_endpoint_returns_printer_status() -> None:
    response = client.get("/api/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["state"] == "printing"
    assert payload["active_job"]["status"] == "running"
    assert len(payload["queued_jobs"]) == 2
    assert len(payload["temperatures"]) == 3
    assert {t["component"] for t in payload["temperatures"]} == {
        "hotend",
        "bed",
        "chamber",
    }


def test_jobs_endpoint_returns_flat_list() -> None:
    response = client.get("/api/jobs")
    assert response.status_code == 200

    jobs = response.json()
    assert len(jobs) == 3
    statuses = {job["status"] for job in jobs}
    assert statuses == {"running", "queued"}
    active_job = jobs[0]
    assert active_job["progress"] == 0.42


def test_temperatures_endpoint_returns_readings() -> None:
    response = client.get("/api/temperatures")
    assert response.status_code == 200

    temperatures = response.json()
    assert len(temperatures) == 3
    for reading in temperatures:
        assert set(reading) >= {"component", "actual", "timestamp"}
        assert isinstance(reading["actual"], (float, int))
