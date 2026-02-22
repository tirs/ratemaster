"""Property events for Engine B.

Revision ID: 006
Revises: 005
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(32), server_default="holiday"),
        sa.Column("multiplier", sa.Numeric(6, 4), server_default="1.1"),
        sa.Column("name", sa.String(128), nullable=True),
    )
    op.create_index("ix_property_events_property_date", "property_events", ["property_id", "event_date"])


def downgrade() -> None:
    op.drop_index("ix_property_events_property_date", "property_events")
    op.drop_table("property_events")
