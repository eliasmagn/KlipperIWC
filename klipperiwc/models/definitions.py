"""Pydantic models representing designer-authored hardware definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

__all__ = [
    "DefinitionCreate",
    "DefinitionUpdate",
    "DefinitionResponse",
]


class DefinitionBase(BaseModel):
    """Shared attributes for persisted board or printer definitions."""

    slug: str = Field(
        ..., pattern=r"^[a-z0-9][a-z0-9_.-]{2,}$", description="Stable identifier used within the registry"
    )
    name: str = Field(..., min_length=1, description="Human readable display name")
    description: Optional[str] = Field(
        None, description="Optional description that appears in listings or search results"
    )
    preview_image_url: Optional[AnyUrl] = Field(
        None,
        description="Optional link to a generated preview image or board photo",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON payload exported from the visual designer",
    )

    model_config = ConfigDict(extra="forbid")


class DefinitionCreate(DefinitionBase):
    """Payload expected when persisting a new definition."""

    model_config = ConfigDict(extra="forbid")


class DefinitionUpdate(BaseModel):
    """Fields that can be updated on an existing definition."""

    name: Optional[str] = Field(None, min_length=1, description="Human readable display name")
    description: Optional[str] = Field(
        None, description="Optional description that appears in listings or search results"
    )
    preview_image_url: Optional[AnyUrl] = Field(
        None,
        description="Optional link to a generated preview image or board photo",
    )
    data: Optional[dict[str, Any]] = Field(
        None,
        description="Arbitrary JSON payload exported from the visual designer",
    )

    model_config = ConfigDict(extra="forbid")


class DefinitionResponse(DefinitionBase):
    """Representation of a persisted definition document."""

    id: str = Field(..., description="Unique identifier for the stored document")
    created_at: datetime = Field(..., description="Timestamp at which the definition was created")
    updated_at: datetime = Field(..., description="Timestamp of the last modification")

    model_config = ConfigDict(extra="forbid")
