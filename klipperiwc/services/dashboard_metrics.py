"""Utility functions to derive aggregated dashboard metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from klipperiwc.db.models import JobHistory, StatusHistory, TemperatureHistory

__all__ = [
    "get_dashboard_overview",
    "get_temperature_summary",
    "get_job_metrics",
]


def _to_isoformat(value: datetime | None) -> str | None:
    """Return the ISO representation of a datetime preserving timezone info."""

    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _map_job(job: JobHistory) -> dict[str, Any]:
    """Convert a :class:`JobHistory` instance into a serialisable structure."""

    return {
        "job_identifier": job.job_identifier,
        "name": job.name,
        "progress": float(job.progress) if job.progress is not None else None,
        "status": job.status_value,
        "started_at": _to_isoformat(job.started_at),
        "estimated_completion": _to_isoformat(job.estimated_completion),
        "is_active": bool(job.is_active),
        "last_seen_at": _to_isoformat(job.created_at),
    }


def get_dashboard_overview(
    session: Session,
    *,
    progress_points: int = 20,
) -> dict[str, Any]:
    """Return a condensed snapshot of the latest printer state."""

    progress_points = max(1, min(progress_points, 200))

    stmt = (
        select(StatusHistory)
        .options(
            selectinload(StatusHistory.jobs),
        )
        .order_by(StatusHistory.recorded_at.desc(), StatusHistory.id.desc())
        .limit(1)
    )
    latest = session.execute(stmt).scalars().first()

    overview: dict[str, Any] = {
        "updated_at": None,
        "state": "unknown",
        "message": None,
        "uptime_seconds": None,
        "active_job": None,
        "queued_jobs": {"count": 0, "entries": []},
        "history": {"progress": []},
    }

    if latest is None:
        return overview

    overview["updated_at"] = _to_isoformat(latest.recorded_at)
    overview["state"] = latest.state
    overview["message"] = latest.message
    overview["uptime_seconds"] = latest.uptime_seconds

    active_job_entity = next((job for job in latest.jobs if job.is_active), None)
    if active_job_entity is not None:
        overview["active_job"] = _map_job(active_job_entity)
    elif latest.active_job_id:
        overview["active_job"] = {
            "job_identifier": latest.active_job_id,
            "name": latest.active_job_name,
            "progress": float(latest.active_job_progress)
            if latest.active_job_progress is not None
            else None,
            "status": latest.active_job_status,
            "started_at": _to_isoformat(latest.active_job_started_at),
            "estimated_completion": _to_isoformat(
                latest.active_job_estimated_completion
            ),
            "is_active": True,
            "last_seen_at": _to_isoformat(latest.recorded_at),
        }

    fallback_timestamp = datetime.min.replace(tzinfo=timezone.utc)
    queued_entries = [
        _map_job(job)
        for job in sorted(
            (job for job in latest.jobs if not job.is_active),
            key=lambda item: item.created_at or fallback_timestamp,
        )
    ]
    overview["queued_jobs"] = {
        "count": len(queued_entries),
        "entries": queued_entries,
    }

    progress_stmt = (
        select(StatusHistory.recorded_at, StatusHistory.active_job_progress)
        .where(StatusHistory.active_job_progress.is_not(None))
        .order_by(StatusHistory.recorded_at.desc(), StatusHistory.id.desc())
        .limit(progress_points)
    )
    progress_rows = session.execute(progress_stmt).all()
    overview["history"]["progress"] = [
        {
            "recorded_at": _to_isoformat(row.recorded_at),
            "progress": float(row.active_job_progress),
        }
        for row in reversed(progress_rows)
        if row.active_job_progress is not None
    ]

    return overview


def get_temperature_summary(session: Session) -> dict[str, Any]:
    """Return aggregated statistics for recorded temperature readings."""

    window_stmt = (
        select(
            TemperatureHistory.id,
            TemperatureHistory.component,
            TemperatureHistory.actual,
            TemperatureHistory.target,
            TemperatureHistory.timestamp,
            func.row_number()
            .over(
                partition_by=TemperatureHistory.component,
                order_by=(
                    TemperatureHistory.timestamp.desc(),
                    TemperatureHistory.id.desc(),
                ),
            )
            .label("row_rank"),
        )
    ).subquery()

    latest_rows = session.execute(
        select(window_stmt).where(window_stmt.c.row_rank == 1)
    ).all()

    stats_stmt = (
        select(
            TemperatureHistory.component,
            func.count(TemperatureHistory.id).label("samples"),
            func.min(TemperatureHistory.actual).label("min_actual"),
            func.max(TemperatureHistory.actual).label("max_actual"),
            func.avg(TemperatureHistory.actual).label("avg_actual"),
        )
        .group_by(TemperatureHistory.component)
        .order_by(TemperatureHistory.component.asc())
    )
    stats_rows = session.execute(stats_stmt).all()

    stats_lookup = {
        row.component: {
            "samples": int(row.samples),
            "min_actual": float(row.min_actual) if row.min_actual is not None else None,
            "max_actual": float(row.max_actual) if row.max_actual is not None else None,
            "avg_actual": float(row.avg_actual) if row.avg_actual is not None else None,
        }
        for row in stats_rows
    }

    components: list[dict[str, Any]] = []
    latest_update: datetime | None = None
    for row in latest_rows:
        component_stats = stats_lookup.get(row.component, {})
        latest_ts = row.timestamp
        if latest_update is None or (
            latest_ts is not None and latest_ts > latest_update
        ):
            latest_update = latest_ts
        components.append(
            {
                "component": row.component,
                "latest": {
                    "actual": float(row.actual) if row.actual is not None else None,
                    "target": float(row.target) if row.target is not None else None,
                    "timestamp": _to_isoformat(row.timestamp),
                },
                "statistics": component_stats,
            }
        )

    components.sort(key=lambda entry: entry["component"])

    return {
        "updated_at": _to_isoformat(latest_update),
        "components": components,
    }


def get_job_metrics(
    session: Session,
    *,
    limit: int = 5,
) -> dict[str, Any]:
    """Return condensed information about recently observed jobs."""

    limit = max(1, min(limit, 50))

    jobs_window = (
        select(
            JobHistory.id,
            JobHistory.job_identifier,
            JobHistory.name,
            JobHistory.progress,
            JobHistory.status_value,
            JobHistory.started_at,
            JobHistory.estimated_completion,
            JobHistory.is_active,
            JobHistory.created_at,
            StatusHistory.recorded_at.label("recorded_at"),
            func.row_number()
            .over(
                partition_by=JobHistory.job_identifier,
                order_by=(
                    StatusHistory.recorded_at.desc(),
                    JobHistory.id.desc(),
                ),
            )
            .label("row_rank"),
        )
        .join(StatusHistory, StatusHistory.id == JobHistory.status_id)
    ).subquery()

    latest_jobs_stmt = (
        select(jobs_window)
        .where(jobs_window.c.row_rank == 1)
        .order_by(
            jobs_window.c.recorded_at.desc(),
            jobs_window.c.id.desc(),
        )
        .limit(limit)
    )
    latest_jobs = session.execute(latest_jobs_stmt).all()

    recent: list[dict[str, Any]] = []
    updated_at: datetime | None = None
    for row in latest_jobs:
        recorded_at = row.recorded_at
        if updated_at is None or (
            recorded_at is not None and recorded_at > updated_at
        ):
            updated_at = recorded_at
        recent.append(
            {
                "job_identifier": row.job_identifier,
                "name": row.name,
                "progress": float(row.progress) if row.progress is not None else None,
                "status": row.status_value,
                "started_at": _to_isoformat(row.started_at),
                "estimated_completion": _to_isoformat(row.estimated_completion),
                "is_active": bool(row.is_active),
                "last_seen_at": _to_isoformat(row.recorded_at),
            }
        )

    totals_stmt = (
        select(
            jobs_window.c.status_value,
            func.count().label("count"),
        )
        .where(jobs_window.c.row_rank == 1)
        .group_by(jobs_window.c.status_value)
    )
    totals_rows = session.execute(totals_stmt).all()

    status_totals = {row.status_value: int(row.count) for row in totals_rows}

    return {
        "updated_at": _to_isoformat(updated_at),
        "recent": recent,
        "status_totals": status_totals,
    }
