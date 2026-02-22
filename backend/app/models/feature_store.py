"""Feature store - computed features per run/date for ML."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class FeatureStore(Base):
    """Computed features per property/run/stay_date for engines and training."""

    __tablename__ = "feature_store"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id")
    )
    run_id: Mapped[str] = mapped_column(String(64))
    stay_date: Mapped[str] = mapped_column(String(10))
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
