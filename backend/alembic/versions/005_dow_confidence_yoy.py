"""DOW rules, min_confidence_threshold, YoY curves support.

Revision ID: 005
Revises: 004
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "dow_rules" not in [c["name"] for c in inspector.get_columns("properties")]:
        op.add_column(
            "properties",
            sa.Column("dow_rules", JSONB, server_default="{}", nullable=True),
        )
    if "min_confidence_threshold" not in [c["name"] for c in inspector.get_columns("properties")]:
        op.add_column(
            "properties",
            sa.Column("min_confidence_threshold", sa.Integer, nullable=True),
        )
    if "yoy_curves" not in inspector.get_table_names():
        op.create_table(
            "yoy_curves",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
            sa.Column("curve_type", sa.String(32), nullable=False),
            sa.Column("bucket", sa.String(32), nullable=False),
            sa.Column("multiplier", sa.Numeric(8, 4), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "yoy_curves" in inspector.get_table_names():
        indexes = [i["name"] for i in inspector.get_indexes("yoy_curves")]
        if "ix_yoy_curves_property" not in indexes:
            op.create_index("ix_yoy_curves_property", "yoy_curves", ["property_id", "curve_type"])


def downgrade() -> None:
    op.drop_index("ix_yoy_curves_property", "yoy_curves")
    op.drop_table("yoy_curves")
    op.drop_column("properties", "min_confidence_threshold")
    op.drop_column("properties", "dow_rules")
