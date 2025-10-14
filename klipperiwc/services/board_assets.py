"""Service helpers for board asset management."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from klipperiwc.db.models import (
    AssetModerationStatus,
    AssetVisibility,
    BoardAsset,
    BoardAssetModerationEvent,
)
from klipperiwc.storage import StorageBackend, get_storage_backend

__all__ = [
    "AssetModerationStatus",
    "AssetVisibility",
    "AssetAlreadyExistsError",
    "create_board_asset",
    "list_board_assets",
    "update_board_asset_metadata",
    "set_board_asset_moderation",
    "list_pending_moderation",
]


class AssetAlreadyExistsError(RuntimeError):
    """Raised when an asset with the same checksum already exists."""


def _normalise_visibility(value: str | None) -> str:
    if not value:
        return AssetVisibility.PRIVATE.value
    try:
        return AssetVisibility(value).value
    except ValueError as exc:  # pragma: no cover - validated at API layer
        raise ValueError(f"Unsupported visibility '{value}'") from exc


async def create_board_asset(
    session: Session,
    *,
    data: bytes,
    filename: str | None,
    content_type: str | None,
    title: str | None,
    description: str | None,
    uploaded_by: str | None,
    visibility: str | None,
) -> BoardAsset:
    """Store the uploaded asset and register metadata."""

    if not data:
        raise ValueError("Uploaded asset is empty")

    max_size = int(os.getenv("BOARD_ASSET_MAX_BYTES", str(20 * 1024 * 1024)))
    if len(data) > max_size:
        raise ValueError("Uploaded asset exceeds the configured size limit")

    checksum = hashlib.sha256(data).hexdigest()

    existing = session.execute(
        select(BoardAsset).where(BoardAsset.checksum_sha256 == checksum)
    ).scalar_one_or_none()
    if existing is not None:
        raise AssetAlreadyExistsError("An asset with this checksum already exists")

    asset_id = str(uuid4())
    original_filename = filename or f"board-{asset_id}.svg"
    extension = Path(original_filename).suffix
    storage_path = f"{asset_id}{extension}"

    backend_name = os.getenv("BOARD_ASSET_STORAGE_BACKEND", "local").lower()
    backend: StorageBackend = get_storage_backend()
    storage_uri = await backend.save(storage_path, data, content_type)

    asset = BoardAsset(
        id=asset_id,
        title=title,
        description=description,
        original_filename=original_filename,
        content_type=content_type,
        file_size=len(data),
        checksum_sha256=checksum,
        storage_backend=backend_name,
        storage_path=storage_path,
        storage_uri=storage_uri,
        uploaded_by=uploaded_by,
        visibility=_normalise_visibility(visibility),
    )
    session.add(asset)

    moderation_event = BoardAssetModerationEvent(
        asset=asset,
        status=AssetModerationStatus.PENDING.value,
        reviewer=None,
        notes="Asset submitted and awaiting review",
        processed_at=None,
    )
    session.add(moderation_event)
    session.commit()
    session.refresh(asset)
    return asset


def list_board_assets(
    session: Session,
    *,
    status: str | None = None,
    visibility: str | None = None,
) -> list[BoardAsset]:
    """Return assets filtered by moderation status and visibility if provided."""

    stmt = select(BoardAsset).order_by(BoardAsset.created_at.desc())
    if status:
        stmt = stmt.where(BoardAsset.moderation_status == status)
    if visibility:
        stmt = stmt.where(BoardAsset.visibility == visibility)
    return list(session.execute(stmt).scalars().all())


def update_board_asset_metadata(
    session: Session,
    *,
    asset_id: str,
    title: str | None,
    description: str | None,
    visibility: str | None,
) -> BoardAsset:
    """Update metadata fields for an asset."""

    asset = session.get(BoardAsset, asset_id)
    if asset is None:
        raise LookupError("Asset not found")

    if title is not None:
        asset.title = title
    if description is not None:
        asset.description = description
    if visibility is not None:
        asset.visibility = _normalise_visibility(visibility)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def set_board_asset_moderation(
    session: Session,
    *,
    asset_id: str,
    status: AssetModerationStatus,
    reviewer: str | None,
    notes: str | None,
) -> BoardAsset:
    """Apply a moderation decision and record an audit event."""

    asset = session.get(BoardAsset, asset_id)
    if asset is None:
        raise LookupError("Asset not found")

    asset.moderation_status = status.value
    asset.reviewed_by = reviewer
    asset.reviewed_at = datetime.now(timezone.utc)
    asset.moderation_notes = notes
    session.add(asset)

    event = BoardAssetModerationEvent(
        asset=asset,
        status=status.value,
        reviewer=reviewer,
        notes=notes,
        processed_at=asset.reviewed_at,
    )
    session.add(event)
    session.commit()
    session.refresh(asset)
    return asset


def list_pending_moderation(session: Session) -> list[BoardAsset]:
    """Return all assets waiting for moderation."""

    stmt = (
        select(BoardAsset)
        .where(BoardAsset.moderation_status == AssetModerationStatus.PENDING.value)
        .order_by(BoardAsset.created_at.asc())
    )
    return list(session.execute(stmt).scalars().all())
