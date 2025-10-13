"""Board asset management endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from klipperiwc.db.session import get_session
from klipperiwc.models import (
    BoardAssetModerationStatus,
    BoardAssetModerationEvent as BoardAssetModerationEventModel,
    BoardAssetModerationUpdate,
    BoardAssetResponse,
    BoardAssetUpdate,
    BoardAssetVisibility,
)
from klipperiwc.services.board_assets import (
    AssetAlreadyExistsError,
    AssetModerationStatus,
    create_board_asset,
    list_board_assets,
    list_pending_moderation,
    set_board_asset_moderation,
    update_board_asset_metadata,
)

router = APIRouter(prefix="/api/board-assets", tags=["board-assets"])


def _require_token(provided: str | None, env_name: str) -> None:
    expected = os.getenv(env_name)
    if expected and provided != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _map_response(asset) -> BoardAssetResponse:
    events = sorted(
        list(asset.moderation_events),
        key=lambda event: event.created_at or event.id,
    )
    return BoardAssetResponse(
        id=asset.id,
        title=asset.title,
        description=asset.description,
        visibility=BoardAssetVisibility(asset.visibility),
        uploaded_by=asset.uploaded_by,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        file_size=asset.file_size,
        checksum_sha256=asset.checksum_sha256,
        storage_backend=asset.storage_backend,
        storage_path=asset.storage_path,
        storage_uri=asset.storage_uri,
        moderation_status=BoardAssetModerationStatus(asset.moderation_status),
        moderation_notes=asset.moderation_notes,
        reviewed_by=asset.reviewed_by,
        reviewed_at=asset.reviewed_at,
        created_at=asset.created_at,
        moderation_events=[
            BoardAssetModerationEventModel.model_validate(event, from_attributes=True)
            for event in events
        ],
    )


@router.post("/", response_model=BoardAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_board_asset(
    file: UploadFile = File(..., description="Board design asset"),
    title: str | None = Form(None),
    description: str | None = Form(None),
    visibility: BoardAssetVisibility = Form(BoardAssetVisibility.PRIVATE),
    uploaded_by: str | None = Form(None),
    session: Session = Depends(get_session),
    access_token: str | None = Header(None, alias="X-Board-Assets-Key"),
) -> BoardAssetResponse:
    """Upload a new board design asset and queue it for moderation."""

    _require_token(access_token, "BOARD_ASSET_UPLOAD_TOKEN")

    data = await file.read()
    try:
        asset = await create_board_asset(
            session,
            data=data,
            filename=file.filename,
            content_type=file.content_type,
            title=title,
            description=description,
            uploaded_by=uploaded_by,
            visibility=visibility.value,
        )
    except AssetAlreadyExistsError as exc:  # pragma: no cover - deterministic conflict path
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _map_response(asset)


@router.get("/", response_model=list[BoardAssetResponse])
async def list_assets(
    status_filter: BoardAssetModerationStatus | None = None,
    session: Session = Depends(get_session),
) -> list[BoardAssetResponse]:
    """List board assets filtered by moderation status."""

    status_value = status_filter.value if status_filter else None
    assets = list_board_assets(session, status=status_value)
    return [_map_response(asset) for asset in assets]


@router.patch("/{asset_id}", response_model=BoardAssetResponse)
async def update_asset_metadata(
    asset_id: str,
    payload: BoardAssetUpdate,
    session: Session = Depends(get_session),
    access_token: str | None = Header(None, alias="X-Board-Assets-Key"),
) -> BoardAssetResponse:
    """Update metadata for a specific asset."""

    _require_token(access_token, "BOARD_ASSET_UPLOAD_TOKEN")

    try:
        asset = update_board_asset_metadata(
            session,
            asset_id=asset_id,
            title=payload.title,
            description=payload.description,
            visibility=payload.visibility.value if payload.visibility else None,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _map_response(asset)


@router.get("/moderation/pending", response_model=list[BoardAssetResponse])
async def list_pending_assets(
    session: Session = Depends(get_session),
    moderator_token: str | None = Header(None, alias="X-Board-Assets-Moderator"),
) -> list[BoardAssetResponse]:
    """Return all assets currently waiting for moderation."""

    _require_token(moderator_token, "BOARD_ASSET_MODERATION_TOKEN")
    assets = list_pending_moderation(session)
    return [_map_response(asset) for asset in assets]


@router.patch("/{asset_id}/moderation", response_model=BoardAssetResponse)
async def update_moderation(
    asset_id: str,
    payload: BoardAssetModerationUpdate,
    session: Session = Depends(get_session),
    moderator_token: str | None = Header(None, alias="X-Board-Assets-Moderator"),
) -> BoardAssetResponse:
    """Approve or reject an asset and record the moderation decision."""

    _require_token(moderator_token, "BOARD_ASSET_MODERATION_TOKEN")

    try:
        status_value = AssetModerationStatus(payload.status.value)
        asset = set_board_asset_moderation(
            session,
            asset_id=asset_id,
            status=status_value,
            reviewer=payload.reviewer,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _map_response(asset)
