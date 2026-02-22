"""Property events - holidays, local events affecting demand."""
from datetime import date
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class PropertyEvent(Base):
    """Event date affecting rate recommendations (e.g. holiday, conference)."""

    __tablename__ = "property_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), default="holiday")
    multiplier: Mapped[float] = mapped_column(Numeric(6, 4), default=1.1)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
