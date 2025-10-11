"""Tests for the status history repository helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from klipperiwc.db import Base
from klipperiwc.db.models import JobHistory, StatusHistory, TemperatureHistory
from klipperiwc.models import JobSummary, PrinterStatus, TemperatureReading
from klipperiwc.repositories.status_history import (
    create_status_history,
    delete_older_than,
    delete_status_history,
    get_status_history,
    list_status_history,
    update_status_history,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def _sample_status(now: datetime) -> PrinterStatus:
    active_job = JobSummary(
        id="job-1",
        name="Calibration cube",
        progress=0.5,
        status="running",
        started_at=now - timedelta(minutes=10),
        estimated_completion=now + timedelta(minutes=10),
    )
    queued_job = JobSummary(
        id="job-2",
        name="Spare part",
        progress=0.0,
        status="queued",
        started_at=None,
        estimated_completion=None,
    )
    temperatures = [
        TemperatureReading(
            component="hotend",
            actual=210.0,
            target=215.0,
            timestamp=now,
        ),
        TemperatureReading(
            component="bed",
            actual=60.0,
            target=60.0,
            timestamp=now,
        ),
    ]
    return PrinterStatus(
        state="printing",
        message="All good",
        uptime_seconds=3600,
        active_job=active_job,
        queued_jobs=[queued_job],
        temperatures=temperatures,
    )


def test_create_status_history_persists_nested_entities(session: Session) -> None:
    now = datetime.now(timezone.utc)
    status = _sample_status(now)

    entry = create_status_history(session, status, recorded_at=now)

    assert entry.id is not None
    assert len(entry.temperatures) == 2
    assert {t.component for t in entry.temperatures} == {"hotend", "bed"}
    assert len(entry.jobs) == 2
    assert any(job.is_active for job in entry.jobs)


def test_get_status_history_returns_entry(session: Session) -> None:
    now = datetime.now(timezone.utc)
    entry = create_status_history(session, _sample_status(now), recorded_at=now)
    session.flush()

    fetched = get_status_history(session, entry.id)
    assert fetched is not None
    assert fetched.state == "printing"
    assert fetched.active_job_name == "Calibration cube"


def test_list_status_history_orders_newest_first(session: Session) -> None:
    base = datetime.now(timezone.utc)
    create_status_history(session, _sample_status(base - timedelta(hours=1)), recorded_at=base - timedelta(hours=1))
    create_status_history(session, _sample_status(base), recorded_at=base)

    results = list_status_history(session)
    normalized = [
        value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        for value in (r.recorded_at for r in results)
    ]
    assert normalized == sorted(normalized, reverse=True)


def test_update_status_history(session: Session) -> None:
    now = datetime.now(timezone.utc)
    entry = create_status_history(session, _sample_status(now), recorded_at=now)

    updated = update_status_history(session, entry.id, message="Updated", state="idle")

    assert updated is not None
    assert updated.message == "Updated"
    assert updated.state == "idle"


def test_delete_status_history_cascades(session: Session) -> None:
    now = datetime.now(timezone.utc)
    entry = create_status_history(session, _sample_status(now), recorded_at=now)

    deleted = delete_status_history(session, entry.id)
    assert deleted is True
    assert session.get(StatusHistory, entry.id) is None
    assert session.execute(select(TemperatureHistory)).scalars().all() == []
    assert session.execute(select(JobHistory)).scalars().all() == []


def test_delete_older_than_removes_expected_rows(session: Session) -> None:
    now = datetime.now(timezone.utc)
    old_entry = create_status_history(session, _sample_status(now - timedelta(days=10)), recorded_at=now - timedelta(days=10))
    new_entry = create_status_history(session, _sample_status(now), recorded_at=now)

    deleted_count = delete_older_than(session, now - timedelta(days=5))

    assert deleted_count == 1
    assert session.get(StatusHistory, old_entry.id) is None
    assert session.get(StatusHistory, new_entry.id) is not None
