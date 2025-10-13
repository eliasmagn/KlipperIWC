"""Pydantic schemas for board asset APIs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModerationStatus(str, Enum):
    """Available moderation states."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssetVisibility(str, Enum):
    """Possible visibility options for an asset."""

    PRIVATE = "private"
    PUBLIC = "public"


class BoardAssetBase(BaseModel):
    """Base schema shared by asset payloads."""

    title: Optional[str] = Field(None, description="Optional title for the board design")
    description: Optional[str] = Field(None, description="Extended description")
    visibility: AssetVisibility = Field(
        AssetVisibility.PRIVATE, description="Controls whether the asset is public or private"
    )
    uploaded_by: Optional[str] = Field(None, description="Identifier of the uploader")


class BoardAssetCreate(BoardAssetBase):
    """Input payload for asset creation."""

    pass


class BoardAssetUpdate(BaseModel):
    """Partial update payload for assets."""

    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[AssetVisibility] = None


class BoardAssetModerationUpdate(BaseModel):
    """Moderation update payload."""

    status: ModerationStatus
    notes: Optional[str] = None
    reviewer: Optional[str] = None


class BoardAssetModerationEvent(BaseModel):
    """Moderation history entry."""

    status: ModerationStatus
    reviewer: Optional[str] = None
    notes: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardAssetResponse(BoardAssetBase):
    """Response payload for assets."""

    id: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: int
    checksum_sha256: str
    storage_backend: str
    storage_path: str
    storage_uri: Optional[str] = None
    moderation_status: ModerationStatus
    moderation_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    moderation_events: list[BoardAssetModerationEvent] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
