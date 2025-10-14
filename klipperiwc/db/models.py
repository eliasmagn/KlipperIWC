"""SQLAlchemy ORM models for KlipperIWC persistence."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

__all__ = [
    "StatusHistory",
    "TemperatureHistory",
    "JobHistory",
    "BoardAsset",
    "BoardAssetModerationEvent",
    "AssetModerationStatus",
    "AssetVisibility",
    "BoardDefinitionDocument",
    "PrinterDefinitionDocument",
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


class AssetModerationStatus(str, Enum):
    """Possible moderation states for uploaded assets."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssetVisibility(str, Enum):
    """Supported visibility values for board assets."""

    PRIVATE = "private"
    PUBLIC = "public"


class BoardAsset(Base, TimestampMixin):
    """Stored board designs and associated metadata."""

    __tablename__ = "board_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    storage_backend: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_uri: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    visibility: Mapped[str] = mapped_column(String(16), default=AssetVisibility.PRIVATE.value, nullable=False, index=True)
    moderation_status: Mapped[str] = mapped_column(
        String(16),
        default=AssetModerationStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    moderation_events: Mapped[list["BoardAssetModerationEvent"]] = relationship(
        "BoardAssetModerationEvent",
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return f"BoardAsset(id={self.id!r}, filename={self.original_filename!r}, status={self.moderation_status!r})"


class BoardAssetModerationEvent(Base, TimestampMixin):
    """Historical moderation decisions for an asset."""

    __tablename__ = "board_asset_moderation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(
        ForeignKey("board_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reviewer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped[BoardAsset] = relationship("BoardAsset", back_populates="moderation_events")

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return f"BoardAssetModerationEvent(id={self.id!r}, asset_id={self.asset_id!r}, status={self.status!r})"


class DefinitionDocumentMixin(TimestampMixin):
    """Common columns for stored board and printer definitions."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_image_uri: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BoardDefinitionDocument(DefinitionDocumentMixin, Base):
    """Persisted board definition document authored in the designer."""

    __tablename__ = "board_definition_documents"


class PrinterDefinitionDocument(DefinitionDocumentMixin, Base):
    """Persisted printer definition document authored in the designer."""

    __tablename__ = "printer_definition_documents"
