"""Market snapshots and outcomes."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class MarketSnapshot(Base):
    """Market rate snapshot with timestamps and source metadata."""

    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    compset_avg: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    compset_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    compset_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(64))
    stay_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Outcome(Base):
    """Imported outcomes/actuals for learning loop."""

    __tablename__ = "outcomes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    stay_date: Mapped[str] = mapped_column(String(10))
    actual_adr: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_occupancy: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    actual_revenue: Mapped[float | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recommendations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
