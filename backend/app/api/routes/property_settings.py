"""Property settings - flow-through, billing, guardrails."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.services.org_access import get_user_org_role, role_can_edit_settings, user_has_property_access

router = APIRouter(prefix="/properties", tags=["property_settings"])


class PropertySettingsUpdate(BaseModel):
    flow_through_pct: Decimal | None = None
    base_monthly_fee: Decimal | None = None
    revenue_share_pct: Decimal | None = None
    revenue_share_on_gop: bool | None = None
    contract_effective_from: date | None = None
    contract_effective_to: date | None = None
    min_bar: Decimal | None = None
    max_bar: Decimal | None = None
    max_daily_change_pct: Decimal | None = None
    blackout_dates: list[str] | None = None
    dow_rules: dict | None = None
    min_confidence_threshold: int | None = None
    market_refresh_minutes: int | None = None


@router.get("/{property_id}/settings")
async def get_property_settings(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get property contract and guardrail settings."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return {
        "flow_through_pct": float(prop.flow_through_pct or 70),
        "base_monthly_fee": float(prop.base_monthly_fee or 0),
        "revenue_share_pct": float(prop.revenue_share_pct or 0),
        "revenue_share_on_gop": prop.revenue_share_on_gop or False,
        "contract_effective_from": prop.contract_effective_from.isoformat() if prop.contract_effective_from else None,
        "contract_effective_to": prop.contract_effective_to.isoformat() if prop.contract_effective_to else None,
        "min_bar": float(prop.min_bar) if prop.min_bar else None,
        "max_bar": float(prop.max_bar) if prop.max_bar else None,
        "max_daily_change_pct": float(prop.max_daily_change_pct) if prop.max_daily_change_pct else None,
        "blackout_dates": prop.blackout_dates or [],
        "dow_rules": prop.dow_rules or {},
        "min_confidence_threshold": prop.min_confidence_threshold,
        "market_refresh_minutes": prop.market_refresh_minutes,
    }


@router.patch("/{property_id}/settings")
async def update_property_settings(
    property_id: str,
    body: PropertySettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update property settings. Owner and GM can edit; Analyst cannot."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    role = await get_user_org_role(db, current_user.id, prop.organization_id)
    if not role_can_edit_settings(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner, Full user, or GM can edit property settings",
        )
    if body.flow_through_pct is not None:
        prop.flow_through_pct = body.flow_through_pct
    if body.base_monthly_fee is not None:
        prop.base_monthly_fee = body.base_monthly_fee
    if body.revenue_share_pct is not None:
        prop.revenue_share_pct = body.revenue_share_pct
    if body.revenue_share_on_gop is not None:
        prop.revenue_share_on_gop = body.revenue_share_on_gop
    if body.contract_effective_from is not None:
        prop.contract_effective_from = body.contract_effective_from
    if body.contract_effective_to is not None:
        prop.contract_effective_to = body.contract_effective_to
    if body.min_bar is not None:
        prop.min_bar = body.min_bar
    if body.max_bar is not None:
        prop.max_bar = body.max_bar
    if body.max_daily_change_pct is not None:
        prop.max_daily_change_pct = body.max_daily_change_pct
    if body.blackout_dates is not None:
        prop.blackout_dates = body.blackout_dates
    if body.dow_rules is not None:
        prop.dow_rules = body.dow_rules
    if body.min_confidence_threshold is not None:
        prop.min_confidence_threshold = body.min_confidence_threshold
    if body.market_refresh_minutes is not None:
        prop.market_refresh_minutes = body.market_refresh_minutes
    await db.flush()
    return {"updated": True}
