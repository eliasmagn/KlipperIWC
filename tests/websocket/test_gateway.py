"""Tests for the websocket gateway."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from klipperiwc.app import create_app
from klipperiwc.models import JobSummary, PrinterStatus, TemperatureReading
from klipperiwc.websocket import status_broadcaster


@pytest.fixture(name="sample_status")
def fixture_sample_status() -> PrinterStatus:
    """Return a deterministic printer status payload for websocket tests."""

    now = datetime.now(timezone.utc)
    return PrinterStatus(
        state="printing",
        message="Fixture status",
        uptime_seconds=123,
        active_job=JobSummary(
            id="job-1",
            name="Test",
            progress=0.5,
            status="running",
            started_at=None,
            estimated_completion=None,
        ),
        queued_jobs=[],
        temperatures=[
            TemperatureReading(
                component="hotend",
                actual=200.0,
                target=210.0,
                timestamp=now,
            ),
        ],
    )


def test_status_websocket_sends_payload_and_disconnects(
    monkeypatch: pytest.MonkeyPatch, sample_status: PrinterStatus
) -> None:
    """The websocket endpoint streams payloads and always disconnects listeners."""

    app = create_app()
    original_connect = status_broadcaster.connect
    original_disconnect = status_broadcaster.disconnect

    async def fake_connect() -> asyncio.Queue[PrinterStatus]:
        queue = await original_connect()
        await queue.put(sample_status)
        return queue

    disconnect_called = False

    async def fake_disconnect(queue: asyncio.Queue[PrinterStatus]) -> None:
        nonlocal disconnect_called
        disconnect_called = True
        await original_disconnect(queue)

    monkeypatch.setattr(status_broadcaster, "connect", fake_connect)
    monkeypatch.setattr(status_broadcaster, "disconnect", fake_disconnect)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/status") as websocket:
            assert status_broadcaster.connection_count == 1
            message = websocket.receive_json()
            assert message["type"] == "status"
            assert message["payload"]["message"] == sample_status.message

    assert disconnect_called is True
    assert status_broadcaster.connection_count == 0


def test_status_websocket_disconnects_on_client_drop(
    monkeypatch: pytest.MonkeyPatch, sample_status: PrinterStatus
) -> None:
    """Dropping the client connection removes the queue from the broadcaster."""

    app = create_app()
    original_connect = status_broadcaster.connect
    original_disconnect = status_broadcaster.disconnect

    async def fake_connect() -> asyncio.Queue[PrinterStatus]:
        queue = await original_connect()
        await queue.put(sample_status)
        return queue

    async def fake_disconnect(queue: asyncio.Queue[PrinterStatus]) -> None:
        await original_disconnect(queue)

    monkeypatch.setattr(status_broadcaster, "connect", fake_connect)
    monkeypatch.setattr(status_broadcaster, "disconnect", fake_disconnect)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/status"):
            assert status_broadcaster.connection_count == 1

    assert status_broadcaster.connection_count == 0
