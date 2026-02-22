"""Engine B strategic calendar entries."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class EngineBCalendar(Base):
    """Engine B 31-365 day rate calendar: floor/target/stretch."""

    __tablename__ = "engine_b_calendar"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    engine_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engine_runs.id")
    )
    stay_date: Mapped[str] = mapped_column(String(10))
    floor: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    target: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    stretch: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    occupancy_forecast_low: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    occupancy_forecast_high: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    why_bullets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
