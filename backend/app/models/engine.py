"""Engine run and recommendation models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Boolean, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class EngineRun(Base):
    """Engine run - immutable record of Engine A or B execution."""

    __tablename__ = "engine_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    engine_type: Mapped[str] = mapped_column(String(32))
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32))
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    why_drivers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Recommendation(Base):
    """Per-stay-date recommendation from engine run."""

    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    engine_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engine_runs.id")
    )
    stay_date: Mapped[str] = mapped_column(String(10))
    suggested_bar: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    current_bar: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    delta_dollars: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    delta_pct: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    occupancy_projection: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    occupancy_projection_low: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    occupancy_projection_high: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    conservative_bar: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    balanced_bar: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    aggressive_bar: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    pickup_projection: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    sellout_probability: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sellout_efficiency: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    revpar_impact: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    why_bullets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
