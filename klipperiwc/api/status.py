"""Status endpoints for KlipperIWC."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from klipperiwc.models import JobSummary, PrinterStatus, TemperatureReading
from klipperiwc.websocket import status_broadcaster
from klipperiwc.services import record_status_snapshot

router = APIRouter(prefix="/api", tags=["status"])


def _demo_temperatures(now: datetime) -> list[TemperatureReading]:
    """Return static demo temperature readings."""

    return [
        TemperatureReading(
            component="hotend",
            actual=205.3,
            target=210.0,
            timestamp=now,
        ),
        TemperatureReading(
            component="bed",
            actual=58.7,
            target=60.0,
            timestamp=now,
        ),
        TemperatureReading(
            component="chamber",
            actual=32.4,
            target=None,
            timestamp=now,
        ),
    ]


def _demo_jobs(now: datetime) -> tuple[JobSummary, list[JobSummary]]:
    """Return demo job data for the mocked API responses."""

    active_job = JobSummary(
        id="job-20240415-01",
        name="Voron_Mount_v6.gcode",
        progress=0.42,
        status="running",
        started_at=now - timedelta(minutes=18),
        estimated_completion=now + timedelta(minutes=25),
    )
    queued_jobs = [
        JobSummary(
            id="job-20240415-02",
            name="Calibration_Cube_20mm.gcode",
            progress=0.0,
            status="queued",
            started_at=None,
            estimated_completion=None,
        ),
        JobSummary(
            id="job-20240415-03",
            name="Mini_Fan_Duct.gcode",
            progress=0.0,
            status="queued",
            started_at=None,
            estimated_completion=None,
        ),
    ]
    return active_job, queued_jobs


@router.get("/status", response_model=PrinterStatus)
async def get_printer_status() -> PrinterStatus:
    """Return the aggregated printer status."""

    now = datetime.now(timezone.utc)
    active_job, queued_jobs = _demo_jobs(now)
    status = PrinterStatus(
        state="printing",
        message="Druck läuft stabil",
        uptime_seconds=4 * 60 * 60 + 32 * 60,
        active_job=active_job,
        queued_jobs=queued_jobs,
        temperatures=_demo_temperatures(now),
    )
    await run_in_threadpool(record_status_snapshot, status)
    await status_broadcaster.publish(status)
    return status


@router.get("/jobs", response_model=list[JobSummary])
async def list_jobs() -> list[JobSummary]:
    """Return the active and queued jobs as a flat list."""

    now = datetime.now(timezone.utc)
    active_job, queued_jobs = _demo_jobs(now)
    return [active_job, *queued_jobs]


@router.get("/temperatures", response_model=list[TemperatureReading])
async def list_temperatures() -> list[TemperatureReading]:
    """Return the latest known temperature readings."""

    now = datetime.now(timezone.utc)
    return _demo_temperatures(now)
