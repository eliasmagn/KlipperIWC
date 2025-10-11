"""Pydantic models describing the printer status domain."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TemperatureReading(BaseModel):
    """Single temperature reading for a printer component."""

    component: str = Field(..., description="Name of the component, e.g. hotend or bed")
    actual: float = Field(..., description="Current measured temperature in °C")
    target: Optional[float] = Field(
        None, description="Target temperature in °C if a setpoint exists"
    )
    timestamp: datetime = Field(..., description="Time when the reading was captured")


class JobSummary(BaseModel):
    """High level information about a queued or running job."""

    id: str = Field(..., description="Internal job identifier")
    name: str = Field(..., description="Human readable job name")
    progress: float = Field(
        ..., ge=0.0, le=1.0, description="Progress value between 0.0 and 1.0"
    )
    status: Literal["queued", "running", "completed", "failed"] = Field(
        ..., description="Execution status of the job"
    )
    started_at: Optional[datetime] = Field(
        None, description="Timestamp when the job started"
    )
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion timestamp for the job"
    )


class PrinterStatus(BaseModel):
    """Aggregated printer status response."""

    state: Literal["idle", "printing", "error", "offline"] = Field(
        ..., description="High level printer state"
    )
    message: Optional[str] = Field(
        None, description="Optional descriptive status message"
    )
    uptime_seconds: Optional[int] = Field(
        None, ge=0, description="Printer uptime in seconds if available"
    )
    active_job: Optional[JobSummary] = Field(
        None, description="Currently active job if one exists"
    )
    queued_jobs: list[JobSummary] = Field(
        default_factory=list,
        description="Jobs waiting to be processed",
    )
    temperatures: list[TemperatureReading] = Field(
        default_factory=list,
        description="Latest temperature readings for relevant components",
    )
