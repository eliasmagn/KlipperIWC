"""SQLAlchemy ORM models for KlipperIWC persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

__all__ = [
    "StatusHistory",
    "TemperatureHistory",
    "JobHistory",
]


class TimestampMixin:
    """Mixin providing created-at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class StatusHistory(Base, TimestampMixin):
    """Historical snapshot of the aggregated printer status."""

    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now, nullable=False, index=True
    )

    active_job_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    active_job_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active_job_progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_job_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    active_job_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    active_job_estimated_completion: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    temperatures: Mapped[list["TemperatureHistory"]] = relationship(
        "TemperatureHistory",
        back_populates="status",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    jobs: Mapped[list["JobHistory"]] = relationship(
        "JobHistory",
        back_populates="status",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return f"StatusHistory(id={self.id!r}, state={self.state!r}, recorded_at={self.recorded_at!r})"


class TemperatureHistory(Base, TimestampMixin):
    """Historical temperature reading for a specific component."""

    __tablename__ = "temperature_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_id: Mapped[int] = mapped_column(
        ForeignKey("status_history.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actual: Mapped[float] = mapped_column(Float, nullable=False)
    target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[StatusHistory] = relationship("StatusHistory", back_populates="temperatures")

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return (
            "TemperatureHistory(id={!r}, component={!r}, timestamp={!r})".format(
                self.id, self.component, self.timestamp
            )
        )


class JobHistory(Base, TimestampMixin):
    """Historical record for active or queued jobs."""

    __tablename__ = "job_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_id: Mapped[int] = mapped_column(
        ForeignKey("status_history.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_identifier: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    progress: Mapped[float] = mapped_column(Float, nullable=False)
    status_value: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[StatusHistory] = relationship("StatusHistory", back_populates="jobs")

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return f"JobHistory(id={self.id!r}, job_identifier={self.job_identifier!r}, status={self.status_value!r})"
