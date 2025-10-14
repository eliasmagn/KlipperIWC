"""Add tables for board and printer definition documents."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20240513_01"
down_revision = "20240512_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "board_definition_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preview_image_uri", sa.String(length=512), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_board_definition_documents_slug",
        "board_definition_documents",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_board_definition_documents_created_at",
        "board_definition_documents",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "printer_definition_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preview_image_uri", sa.String(length=512), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_printer_definition_documents_slug",
        "printer_definition_documents",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_printer_definition_documents_created_at",
        "printer_definition_documents",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_printer_definition_documents_created_at", table_name="printer_definition_documents")
    op.drop_index("ix_printer_definition_documents_slug", table_name="printer_definition_documents")
    op.drop_table("printer_definition_documents")
    op.drop_index("ix_board_definition_documents_created_at", table_name="board_definition_documents")
    op.drop_index("ix_board_definition_documents_slug", table_name="board_definition_documents")
    op.drop_table("board_definition_documents")
