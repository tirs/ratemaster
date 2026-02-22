"""Engine A full outputs, Engine B calendar storage.

Revision ID: 004
Revises: 003
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("conservative_bar", sa.Numeric(12, 2), nullable=True))
    op.add_column("recommendations", sa.Column("balanced_bar", sa.Numeric(12, 2), nullable=True))
    op.add_column("recommendations", sa.Column("aggressive_bar", sa.Numeric(12, 2), nullable=True))
    op.add_column("recommendations", sa.Column("pickup_projection", sa.Numeric(8, 2), nullable=True))
    op.add_column("recommendations", sa.Column("sellout_probability", sa.Numeric(5, 2), nullable=True))
    op.add_column("recommendations", sa.Column("sellout_efficiency", sa.Numeric(5, 2), nullable=True))
    op.add_column("recommendations", sa.Column("revpar_impact", sa.Numeric(8, 2), nullable=True))
    op.add_column("recommendations", sa.Column("confidence_level", sa.String(16), nullable=True))

    op.create_table(
        "engine_b_calendar",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("engine_run_id", sa.String(36), sa.ForeignKey("engine_runs.id"), nullable=False),
        sa.Column("stay_date", sa.String(10), nullable=False),
        sa.Column("floor", sa.Numeric(12, 2), nullable=True),
        sa.Column("target", sa.Numeric(12, 2), nullable=True),
        sa.Column("stretch", sa.Numeric(12, 2), nullable=True),
        sa.Column("occupancy_forecast_low", sa.Numeric(6, 2), nullable=True),
        sa.Column("occupancy_forecast_high", sa.Numeric(6, 2), nullable=True),
        sa.Column("confidence", sa.Integer, nullable=True),
        sa.Column("why_bullets", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("engine_b_calendar")
    op.drop_column("recommendations", "confidence_level")
    op.drop_column("recommendations", "revpar_impact")
    op.drop_column("recommendations", "sellout_efficiency")
    op.drop_column("recommendations", "sellout_probability")
    op.drop_column("recommendations", "pickup_projection")
    op.drop_column("recommendations", "aggressive_bar")
    op.drop_column("recommendations", "balanced_bar")
    op.drop_column("recommendations", "conservative_bar")
