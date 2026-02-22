"""Occupancy projection range and market snapshot linkage.

Revision ID: 007
Revises: 006
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("occupancy_projection_low", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("occupancy_projection_high", sa.Numeric(6, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "occupancy_projection_high")
    op.drop_column("recommendations", "occupancy_projection_low")
