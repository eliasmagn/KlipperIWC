"""Create initial printer status tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20240510_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "printer_status",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("printer_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("printer_name", name="uq_printer_status_printer_name"),
    )

    op.create_table(
        "temperature_readings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("printer_id", sa.Integer(), nullable=False),
        sa.Column("extruder_temp", sa.Float(), nullable=True),
        sa.Column("bed_temp", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["printer_id"], ["printer_status.id"], ondelete="CASCADE"),
        sa.Index("ix_temperature_readings_printer_id_recorded_at", "printer_id", "recorded_at"),
    )


def downgrade() -> None:
    op.drop_table("temperature_readings")
    op.drop_table("printer_status")
