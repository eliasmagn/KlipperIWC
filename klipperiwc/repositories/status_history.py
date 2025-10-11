"""Repository helpers for working with status history records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from klipperiwc.db.models import JobHistory, StatusHistory, TemperatureHistory
from klipperiwc.models import JobSummary, PrinterStatus, TemperatureReading

__all__ = [
    "create_status_history",
    "get_status_history",
    "list_status_history",
    "update_status_history",
    "delete_status_history",
    "delete_older_than",
]


def _build_temperature_entities(
    readings: Iterable[TemperatureReading],
) -> list[TemperatureHistory]:
    return [
        TemperatureHistory(
            component=reading.component,
            actual=reading.actual,
            target=reading.target,
            timestamp=reading.timestamp,
        )
        for reading in readings
    ]


def _build_job_entities(
    active_job: JobSummary | None,
    queued_jobs: Sequence[JobSummary],
) -> list[JobHistory]:
    jobs: list[JobHistory] = []
    if active_job is not None:
        jobs.append(
            JobHistory(
                job_identifier=active_job.id,
                name=active_job.name,
                progress=active_job.progress,
                status_value=active_job.status,
                started_at=active_job.started_at,
                estimated_completion=active_job.estimated_completion,
                is_active=True,
            )
        )
    for job in queued_jobs:
        jobs.append(
            JobHistory(
                job_identifier=job.id,
                name=job.name,
                progress=job.progress,
                status_value=job.status,
                started_at=job.started_at,
                estimated_completion=job.estimated_completion,
                is_active=False,
            )
        )
    return jobs


def create_status_history(
    session: Session,
    status: PrinterStatus,
    recorded_at: datetime | None = None,
) -> StatusHistory:
    """Persist a printer status snapshot and nested entities."""

    timestamp = recorded_at or datetime.now(timezone.utc)
    db_status = StatusHistory(
        state=status.state,
        message=status.message,
        uptime_seconds=status.uptime_seconds,
        recorded_at=timestamp,
        active_job_id=status.active_job.id if status.active_job else None,
        active_job_name=status.active_job.name if status.active_job else None,
        active_job_progress=status.active_job.progress if status.active_job else None,
        active_job_status=status.active_job.status if status.active_job else None,
        active_job_started_at=status.active_job.started_at if status.active_job else None,
        active_job_estimated_completion=
            status.active_job.estimated_completion if status.active_job else None,
    )
    db_status.temperatures = _build_temperature_entities(status.temperatures)
    db_status.jobs = _build_job_entities(status.active_job, status.queued_jobs)

    session.add(db_status)
    session.flush()
    return db_status


def get_status_history(session: Session, status_id: int) -> StatusHistory | None:
    """Return a single status history entry by id."""

    return session.get(StatusHistory, status_id)


def list_status_history(
    session: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[StatusHistory]:
    """Return an ordered list of status history entries (newest first)."""

    stmt = (
        select(StatusHistory)
        .order_by(StatusHistory.recorded_at.desc(), StatusHistory.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.execute(stmt).scalars().all())


def update_status_history(
    session: Session,
    status_id: int,
    **fields: object,
) -> StatusHistory | None:
    """Update mutable columns of a status history entry."""

    entry = session.get(StatusHistory, status_id)
    if entry is None:
        return None

    mutable_fields = {
        "state",
        "message",
        "uptime_seconds",
        "recorded_at",
        "active_job_id",
        "active_job_name",
        "active_job_progress",
        "active_job_status",
        "active_job_started_at",
        "active_job_estimated_completion",
    }

    for key, value in fields.items():
        if key in mutable_fields:
            setattr(entry, key, value)
    session.flush()
    return entry


def delete_status_history(session: Session, status_id: int) -> bool:
    """Delete a status history entry by id."""

    entry = session.get(StatusHistory, status_id)
    if entry is None:
        return False
    session.delete(entry)
    session.flush()
    return True


def delete_older_than(session: Session, before: datetime) -> int:
    """Delete status entries (and cascade data) recorded before *before*."""

    stmt = delete(StatusHistory).where(StatusHistory.recorded_at < before)
    result = session.execute(stmt)
    # Synchronize relationships via ON DELETE CASCADE.
    session.flush()
    return result.rowcount or 0
