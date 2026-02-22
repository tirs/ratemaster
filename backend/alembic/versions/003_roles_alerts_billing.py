"""Roles, alerts, property settings, billing, market snapshots.

Revision ID: 003
Revises: 002
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "org_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_org_members_org", "org_members", ["organization_id", "user_id"], unique=True)

    op.add_column("properties", sa.Column("flow_through_pct", sa.Numeric(5, 2), server_default="70"))
    op.add_column("properties", sa.Column("base_monthly_fee", sa.Numeric(12, 2), server_default="0"))
    op.add_column("properties", sa.Column("revenue_share_pct", sa.Numeric(5, 2), server_default="0"))
    op.add_column("properties", sa.Column("revenue_share_on_gop", sa.Boolean, server_default="false"))
    op.add_column("properties", sa.Column("contract_effective_from", sa.Date(), nullable=True))
    op.add_column("properties", sa.Column("contract_effective_to", sa.Date(), nullable=True))
    op.add_column("properties", sa.Column("min_bar", sa.Numeric(12, 2), nullable=True))
    op.add_column("properties", sa.Column("max_bar", sa.Numeric(12, 2), nullable=True))
    op.add_column("properties", sa.Column("max_daily_change_pct", sa.Numeric(5, 2), nullable=True))
    op.add_column("properties", sa.Column("blackout_dates", JSONB, server_default="[]"))

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("acknowledged", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_org", "alerts", ["organization_id"])
    op.create_index("ix_alerts_property", "alerts", ["property_id"])

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("compset_avg", sa.Numeric(12, 2), nullable=True),
        sa.Column("compset_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("compset_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_market_snapshots_property", "market_snapshots", ["property_id"])

    op.create_table(
        "outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("stay_date", sa.String(10), nullable=False),
        sa.Column("actual_adr", sa.Numeric(12, 2), nullable=True),
        sa.Column("actual_occupancy", sa.Numeric(6, 2), nullable=True),
        sa.Column("actual_revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("recommendations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("outcomes")
    op.drop_table("market_snapshots")
    op.drop_table("alerts")
    op.drop_column("properties", "blackout_dates")
    op.drop_column("properties", "max_daily_change_pct")
    op.drop_column("properties", "max_bar")
    op.drop_column("properties", "min_bar")
    op.drop_column("properties", "contract_effective_to")
    op.drop_column("properties", "contract_effective_from")
    op.drop_column("properties", "revenue_share_on_gop")
    op.drop_column("properties", "revenue_share_pct")
    op.drop_column("properties", "base_monthly_fee")
    op.drop_column("properties", "flow_through_pct")
    op.drop_table("org_members")
