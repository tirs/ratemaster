"""Property events - holidays, local events for Engine B."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.property_event import PropertyEvent
from app.models.organization import Property
from app.models.user import User
from app.services.org_access import user_has_property_access

router = APIRouter(prefix="/properties", tags=["property_events"])


class PropertyEventCreate(BaseModel):
    event_date: date
    event_type: str = "holiday"
    multiplier: float = Field(1.1, ge=0.5, le=2.0)
    name: str | None = None


@router.get("/{property_id}/events")
async def list_property_events(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events for property (holidays, conferences, etc)."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    result = await db.execute(
        select(PropertyEvent)
        .where(PropertyEvent.property_id == property_id)
        .order_by(PropertyEvent.event_date)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "event_date": e.event_date.isoformat(),
            "event_type": e.event_type,
            "multiplier": float(e.multiplier),
            "name": e.name,
        }
        for e in events
    ]


@router.post("/{property_id}/events")
async def create_property_event(
    property_id: str,
    body: PropertyEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add event (holiday, conference) affecting Engine B rates."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    evt = PropertyEvent(
        property_id=property_id,
        event_date=body.event_date,
        event_type=body.event_type,
        multiplier=Decimal(str(body.multiplier)),
        name=body.name,
    )
    db.add(evt)
    await db.flush()
    return {"id": evt.id, "event_date": evt.event_date.isoformat()}


@router.delete("/{property_id}/events/{event_id}")
async def delete_property_event(
    property_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove event."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    result = await db.execute(
        select(PropertyEvent).where(
            PropertyEvent.id == event_id,
            PropertyEvent.property_id == property_id,
        )
    )
    evt = result.scalar_one_or_none()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(evt)
    await db.flush()
    return {"deleted": True}
