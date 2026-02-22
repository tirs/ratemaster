"""Add organization logo_url.

Revision ID: 009
Revises: 008
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("logo_url", sa.String(512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organizations", "logo_url")
