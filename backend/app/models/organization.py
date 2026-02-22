"""Organization and property models."""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid


class Organization(Base, TimestampMixin):
    """Portfolio owner organization."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    properties: Mapped[list["Property"]] = relationship(
        "Property", back_populates="organization"
    )


class Property(Base, TimestampMixin):
    """Hotel property under an organization."""

    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id")
    )
    flow_through_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("70")
    )
    base_monthly_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    revenue_share_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    revenue_share_on_gop: Mapped[bool] = mapped_column(Boolean, default=False)
    contract_effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    min_bar: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_bar: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_daily_change_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    blackout_dates: Mapped[list] = mapped_column(JSONB, default=list)
    dow_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    min_confidence_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_refresh_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_market_refresh_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="properties"
    )
