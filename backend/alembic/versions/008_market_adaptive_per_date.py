"""Adaptive market cadence and per-stay-date market rates.

Revision ID: 008
Revises: 007
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("market_refresh_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column("last_market_refresh_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "market_snapshots",
        sa.Column("stay_date", sa.String(10), nullable=True),
    )
    op.create_index(
        "ix_market_snapshots_property_stay",
        "market_snapshots",
        ["property_id", "stay_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_snapshots_property_stay", "market_snapshots")
    op.drop_column("market_snapshots", "stay_date")
    op.drop_column("properties", "last_market_refresh_at")
    op.drop_column("properties", "market_refresh_minutes")
