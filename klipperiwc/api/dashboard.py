"""Dashboard endpoints exposing aggregated metrics for widgets."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from klipperiwc.db.session import get_session
from klipperiwc.services.dashboard_metrics import (
    get_dashboard_overview,
    get_job_metrics,
    get_temperature_summary,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview(
    session: Session = Depends(get_session),
    progress_points: int = Query(
        20,
        ge=1,
        le=200,
        description="Number of historical progress data points to include",
    ),
) -> dict:
    """Return consolidated printer state information for dashboard widgets."""

    return get_dashboard_overview(session, progress_points=progress_points)


@router.get("/temperatures")
def dashboard_temperatures(session: Session = Depends(get_session)) -> dict:
    """Return temperature summaries per component."""

    return get_temperature_summary(session)


@router.get("/jobs")
def dashboard_jobs(
    session: Session = Depends(get_session),
    limit: int = Query(
        5,
        ge=1,
        le=50,
        description="Maximum number of recent jobs to include",
    ),
) -> dict:
    """Return aggregated information about recently observed jobs."""

    return get_job_metrics(session, limit=limit)
