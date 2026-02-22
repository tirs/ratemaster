"""Property events - lookup multiplier for Engine B."""
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property_event import PropertyEvent


def get_event_multiplier(db: Session, property_id: str, stay_date: str) -> float:
    """Get event multiplier for stay_date. Returns 1.0 if no event."""
    try:
        d = date.fromisoformat(stay_date)
    except (ValueError, TypeError):
        return 1.0
    result = db.execute(
        select(PropertyEvent).where(
            PropertyEvent.property_id == property_id,
            PropertyEvent.event_date == d,
        )
    )
    evt = result.scalar_one_or_none()
    if evt:
        return float(evt.multiplier)
    return 1.0
