"""YoY trend curves by season/month and day-of-week."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class YoYCurve(Base):
    """YoY trend multiplier by curve_type (season/month, dow) and bucket."""

    __tablename__ = "yoy_curves"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    curve_type: Mapped[str] = mapped_column(String(32))
    bucket: Mapped[str] = mapped_column(String(32))
    multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
