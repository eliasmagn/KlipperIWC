"""Add board asset storage tables

Revision ID: 20240512_01
Revises: 20240510_01_initial_tables
Create Date: 2024-05-12 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240512_01"
down_revision = "20240510_01_initial_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "board_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_backend", sa.String(length=32), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("storage_uri", sa.String(length=512), nullable=True),
        sa.Column("uploaded_by", sa.String(length=128), nullable=True),
        sa.Column("visibility", sa.String(length=16), nullable=False, server_default="private"),
        sa.Column("moderation_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("moderation_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("checksum_sha256", name="uq_board_assets_checksum"),
    )
    op.create_index("ix_board_assets_uploaded_by", "board_assets", ["uploaded_by"], unique=False)
    op.create_index("ix_board_assets_visibility", "board_assets", ["visibility"], unique=False)
    op.create_index(
        "ix_board_assets_moderation_status", "board_assets", ["moderation_status"], unique=False
    )

    op.create_table(
        "board_asset_moderation_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.String(length=36), sa.ForeignKey("board_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_board_asset_moderation_events_asset_id",
        "board_asset_moderation_events",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_board_asset_moderation_events_status",
        "board_asset_moderation_events",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_board_asset_moderation_events_status", table_name="board_asset_moderation_events")
    op.drop_index("ix_board_asset_moderation_events_asset_id", table_name="board_asset_moderation_events")
    op.drop_table("board_asset_moderation_events")
    op.drop_index("ix_board_assets_moderation_status", table_name="board_assets")
    op.drop_index("ix_board_assets_visibility", table_name="board_assets")
    op.drop_index("ix_board_assets_uploaded_by", table_name="board_assets")
    op.drop_table("board_assets")
