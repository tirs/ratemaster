"""Manual data entry fallback."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.services.org_access import user_has_property_access

router = APIRouter(prefix="/manual-data", tags=["manual_data"])


class ManualRow(BaseModel):
    stay_date: str = Field(..., description="YYYY-MM-DD")
    rooms_available: int | None = None
    total_rooms: int | None = None
    rooms_sold: int | None = None
    adr: float | None = None
    total_rate: float | None = None
    revenue: float | None = None


class ManualEntryRequest(BaseModel):
    property_id: str
    snapshot_type: str = Field("current", pattern="^(current|prior_year)$")
    rows: list[ManualRow]


@router.post("/entry")
async def manual_entry(
    body: ManualEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual entry fallback for single or batch rows."""
    if not await user_has_property_access(db, current_user.id, body.property_id):
        raise HTTPException(status_code=404, detail="Property not found")

    mapping = {
        "stay_date": "stay_date",
        "rooms_available": "rooms_available",
        "total_rooms": "total_rooms",
        "rooms_sold": "rooms_sold",
        "adr": "adr",
        "total_rate": "total_rate",
        "revenue": "revenue",
    }
    from app.services.data_import import compute_data_health

    rows = [
        {
            "stay_date": r.stay_date,
            "rooms_available": r.rooms_available,
            "total_rooms": r.total_rooms,
            "rooms_sold": r.rooms_sold,
            "adr": r.adr,
            "total_rate": r.total_rate,
            "revenue": r.revenue,
            "raw_data": {},
        }
        for r in body.rows
    ]
    health, fixes = compute_data_health(rows, [])

    snapshot = DataSnapshot(
        property_id=body.property_id,
        snapshot_type=body.snapshot_type,
        column_mapping=mapping,
        row_count=len(rows),
        validation_errors={"recommended_fixes": fixes} if fixes else None,
        data_health_score=health,
    )
    db.add(snapshot)
    await db.flush()

    for r in rows:
        row_obj = DataSnapshotRow(
            snapshot_id=snapshot.id,
            stay_date=r["stay_date"],
            rooms_available=r.get("rooms_available"),
            total_rooms=r.get("total_rooms"),
            rooms_sold=r.get("rooms_sold"),
            adr=r.get("adr"),
            total_rate=r.get("total_rate"),
            revenue=r.get("revenue"),
            raw_data=r.get("raw_data", {}),
        )
        db.add(row_obj)

    return {
        "snapshot_id": snapshot.id,
        "row_count": len(rows),
        "data_health_score": health,
        "recommended_fixes": fixes,
    }
