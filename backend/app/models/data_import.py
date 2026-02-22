"""Data import and snapshot models."""
from sqlalchemy import ForeignKey, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid


class DataSnapshot(Base, TimestampMixin):
    """Snapshot of imported data (current or prior year)."""

    __tablename__ = "data_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    snapshot_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # YYYY-MM-DD logical snapshot date
    snapshot_type: Mapped[str] = mapped_column(
        String(32)
    )  # "current" | "prior_year"
    column_mapping: Mapped[dict] = mapped_column(JSONB, default=dict)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_health_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100


class DataSnapshotRow(Base):
    """Individual row from a data snapshot (denormalized for querying)."""

    __tablename__ = "data_snapshot_rows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_snapshots.id")
    )
    stay_date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    rooms_available: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rooms_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adr: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_rate: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
