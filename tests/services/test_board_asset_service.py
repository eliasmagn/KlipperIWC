"""Unit tests for the board asset service helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from klipperiwc.db import Base
from klipperiwc.db.models import AssetModerationStatus, BoardAsset
from klipperiwc.services.board_assets import list_board_assets


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine)


def _make_asset(
    *,
    id_: str,
    visibility: str,
    status: str,
) -> BoardAsset:
    return BoardAsset(
        id=id_,
        title=f"Asset {id_}",
        description="",
        original_filename=f"asset-{id_}.svg",
        content_type="image/svg+xml",
        file_size=10,
        checksum_sha256=f"checksum-{id_}",
        storage_backend="local",
        storage_path=f"{id_}.svg",
        storage_uri=f"http://localhost/{id_}.svg",
        uploaded_by="tester",
        visibility=visibility,
        moderation_status=status,
        created_at=datetime.now(timezone.utc),
    )


def test_list_board_assets_filters_visibility_and_status(session: Session) -> None:
    approved_public = _make_asset(
        id_="1",
        visibility="public",
        status=AssetModerationStatus.APPROVED.value,
    )
    pending_public = _make_asset(
        id_="2",
        visibility="public",
        status=AssetModerationStatus.PENDING.value,
    )
    approved_private = _make_asset(
        id_="3",
        visibility="private",
        status=AssetModerationStatus.APPROVED.value,
    )

    session.add_all([approved_public, pending_public, approved_private])
    session.commit()

    public_only = list_board_assets(
        session,
        status=AssetModerationStatus.APPROVED.value,
        visibility="public",
    )
    assert [asset.id for asset in public_only] == ["1"]

    pending_only = list_board_assets(
        session,
        status=AssetModerationStatus.PENDING.value,
    )
    assert [asset.id for asset in pending_only] == ["2"]

    all_assets = list_board_assets(session)
    assert sorted(asset.id for asset in all_assets) == ["1", "2", "3"]
