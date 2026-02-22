"""Data snapshots, engine runs, recommendations.

Revision ID: 002
Revises: 001
Create Date: 2025-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("snapshot_date", sa.String(10), nullable=True),
        sa.Column("snapshot_type", sa.String(32), nullable=False),
        sa.Column("column_mapping", JSONB, server_default="{}"),
        sa.Column("row_count", sa.Integer, server_default="0"),
        sa.Column("validation_errors", JSONB, nullable=True),
        sa.Column("data_health_score", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "data_snapshot_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36), sa.ForeignKey("data_snapshots.id"), nullable=False),
        sa.Column("stay_date", sa.String(10), nullable=False),
        sa.Column("rooms_available", sa.Integer, nullable=True),
        sa.Column("total_rooms", sa.Integer, nullable=True),
        sa.Column("rooms_sold", sa.Integer, nullable=True),
        sa.Column("adr", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("raw_data", JSONB, server_default="{}"),
    )

    op.create_table(
        "engine_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("engine_type", sa.String(32), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("inputs", JSONB, server_default="{}"),
        sa.Column("outputs", JSONB, server_default="{}"),
        sa.Column("confidence", sa.Integer, nullable=True),
        sa.Column("why_drivers", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_engine_runs_run_id", "engine_runs", ["run_id"], unique=True)
    op.create_index("ix_engine_runs_property", "engine_runs", ["property_id", "engine_type"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("engine_run_id", sa.String(36), sa.ForeignKey("engine_runs.id"), nullable=False),
        sa.Column("stay_date", sa.String(10), nullable=False),
        sa.Column("suggested_bar", sa.Numeric(12, 2), nullable=True),
        sa.Column("current_bar", sa.Numeric(12, 2), nullable=True),
        sa.Column("delta_dollars", sa.Numeric(12, 2), nullable=True),
        sa.Column("delta_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("occupancy_projection", sa.Numeric(6, 2), nullable=True),
        sa.Column("confidence", sa.Integer, nullable=True),
        sa.Column("why_bullets", JSONB, nullable=True),
        sa.Column("applied", sa.Boolean, server_default="false"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "model_registry",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=True),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_model_registry_name", "model_registry", ["model_name", "version"])

    op.create_table(
        "feature_store",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("stay_date", sa.String(10), nullable=False),
        sa.Column("features", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "background_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("celery_task_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("property_id", sa.String(36), sa.ForeignKey("properties.id"), nullable=True),
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("background_jobs")
    op.drop_table("feature_store")
    op.drop_table("model_registry")
    op.drop_table("recommendations")
    op.drop_table("engine_runs")
    op.drop_table("data_snapshot_rows")
    op.drop_table("data_snapshots")
