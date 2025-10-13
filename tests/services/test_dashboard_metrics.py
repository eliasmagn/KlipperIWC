"""Tests for the dashboard metrics service helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from klipperiwc.db import Base
from klipperiwc.models import JobSummary, PrinterStatus, TemperatureReading
from klipperiwc.repositories.status_history import create_status_history
from klipperiwc.services.dashboard_metrics import (
    get_dashboard_overview,
    get_job_metrics,
    get_temperature_summary,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    session = TestingSession()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def _status(
    *,
    now: datetime,
    progress: float,
    temp_offset: float,
    job_id: str = "job-1",
    job_status: str = "running",
    queued_ids: tuple[str, ...] = (),
) -> PrinterStatus:
    active_job = JobSummary(
        id=job_id,
        name="Calibration cube",
        progress=progress,
        status=job_status,
        started_at=now - timedelta(minutes=10),
        estimated_completion=now + timedelta(minutes=10),
    )
    queued_jobs = [
        JobSummary(
            id=qid,
            name=f"Queued {qid}",
            progress=0.0,
            status="queued",
            started_at=None,
            estimated_completion=None,
        )
        for qid in queued_ids
    ]
    temperatures = [
        TemperatureReading(
            component="hotend",
            actual=210.0 + temp_offset,
            target=215.0,
            timestamp=now,
        ),
        TemperatureReading(
            component="bed",
            actual=60.0 + temp_offset,
            target=60.0,
            timestamp=now,
        ),
    ]
    return PrinterStatus(
        state="printing",
        message="All good",
        uptime_seconds=3600,
        active_job=active_job,
        queued_jobs=queued_jobs,
        temperatures=temperatures,
    )


def test_get_dashboard_overview_returns_latest_state(session: Session) -> None:
    base = datetime.now(timezone.utc)
    create_status_history(session, _status(now=base - timedelta(minutes=5), progress=0.25, temp_offset=-2.0), recorded_at=base - timedelta(minutes=5))
    create_status_history(session, _status(now=base, progress=0.55, temp_offset=0.0, queued_ids=("job-queued",)), recorded_at=base)

    overview = get_dashboard_overview(session, progress_points=5)

    assert overview["state"] == "printing"
    assert overview["active_job"]["progress"] == pytest.approx(0.55)
    assert overview["queued_jobs"]["count"] == 1
    assert overview["history"]["progress"][-1]["progress"] == pytest.approx(0.55)


def test_get_temperature_summary_aggregates_statistics(session: Session) -> None:
    base = datetime.now(timezone.utc)
    create_status_history(session, _status(now=base - timedelta(minutes=3), progress=0.2, temp_offset=-5.0), recorded_at=base - timedelta(minutes=3))
    create_status_history(session, _status(now=base, progress=0.4, temp_offset=3.0), recorded_at=base)

    summary = get_temperature_summary(session)

    assert summary["components"]
    hotend = next(item for item in summary["components"] if item["component"] == "hotend")
    assert hotend["statistics"]["samples"] == 2
    assert hotend["statistics"]["min_actual"] < hotend["statistics"]["max_actual"]
    assert hotend["latest"]["actual"] == pytest.approx(213.0)


def test_get_job_metrics_returns_unique_jobs(session: Session) -> None:
    base = datetime.now(timezone.utc)
    create_status_history(session, _status(now=base - timedelta(minutes=4), progress=0.2, temp_offset=0.0), recorded_at=base - timedelta(minutes=4))
    # Same job later with different progress
    create_status_history(session, _status(now=base - timedelta(minutes=2), progress=0.6, temp_offset=0.0), recorded_at=base - timedelta(minutes=2))
    # Completed job snapshot
    create_status_history(
        session,
        _status(
            now=base,
            progress=1.0,
            temp_offset=0.0,
            job_status="completed",
            job_id="job-2",
        ),
        recorded_at=base,
    )

    metrics = get_job_metrics(session, limit=5)

    identifiers = {item["job_identifier"] for item in metrics["recent"]}
    assert identifiers >= {"job-1", "job-2"}
    assert metrics["status_totals"]["running"] >= 1
    assert metrics["status_totals"]["completed"] == 1
