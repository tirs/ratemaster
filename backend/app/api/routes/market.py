"""Market snapshots API - store and retrieve."""
import io
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.market import MarketSnapshot
from app.services.org_access import user_has_property_access

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/snapshot")
async def create_market_snapshot(
    background_tasks: BackgroundTasks,
    property_id: str = Form(...),
    compset_avg: float | None = Form(None),
    compset_min: float | None = Form(None),
    compset_max: float | None = Form(None),
    source: str = Form("manual"),
    stay_date: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store market snapshot (manual entry or from adapter)."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")

    snapshot = MarketSnapshot(
        property_id=property_id,
        compset_avg=compset_avg,
        compset_min=compset_min,
        compset_max=compset_max,
        source=source,
        stay_date=stay_date,
    )
    db.add(snapshot)
    await db.flush()
    if background_tasks:
        from app.tasks.engine import run_engine_a
        background_tasks.add_task(run_engine_a.delay, property_id)
    return {
        "id": snapshot.id,
        "property_id": property_id,
        "compset_avg": compset_avg,
        "source": source,
    }


@router.get("/snapshots")
async def list_market_snapshots(
    property_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List market snapshots for property."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")

    result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.property_id == property_id)
        .order_by(MarketSnapshot.snapshot_at.desc())
        .limit(limit)
    )
    snapshots = result.scalars().all()
    return [
        {
            "id": s.id,
            "compset_avg": float(s.compset_avg) if s.compset_avg else None,
            "compset_min": float(s.compset_min) if s.compset_min else None,
            "compset_max": float(s.compset_max) if s.compset_max else None,
            "source": s.source,
            "stay_date": s.stay_date,
            "snapshot_at": s.snapshot_at.isoformat(),
        }
        for s in snapshots
    ]


@router.post("/import-csv")
async def import_market_csv(
    background_tasks: BackgroundTasks,
    property_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import market/rate-shop CSV. Columns: stay_date or date, compset_avg or adr."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")

    header_norm = {str(h).strip().lower().replace(" ", "_"): h for h in df.columns}
    date_col = header_norm.get("stay_date") or header_norm.get("date")
    avg_col = header_norm.get("compset_avg") or header_norm.get("adr") or header_norm.get("rate")
    min_col = header_norm.get("compset_min")
    max_col = header_norm.get("compset_max")

    if not date_col or not avg_col:
        raise HTTPException(
            status_code=400,
            detail="CSV must have stay_date/date and compset_avg/adr columns",
        )

    count = 0
    for _, row in df.iterrows():
        val = row.get(date_col)
        if pd.isna(val):
            continue
        try:
            stay_str = pd.to_datetime(val).date().isoformat()
        except (ValueError, TypeError):
            continue
        avg = float(row[avg_col]) if pd.notna(row.get(avg_col)) else None
        if avg is None:
            continue
        mn = float(row[min_col]) if min_col and pd.notna(row.get(min_col)) else None
        mx = float(row[max_col]) if max_col and pd.notna(row.get(max_col)) else None

        snap = MarketSnapshot(
            property_id=property_id,
            compset_avg=avg,
            compset_min=mn,
            compset_max=mx,
            source="customer_csv",
            stay_date=stay_str,
        )
        db.add(snap)
        count += 1

    await db.flush()
    if count > 0 and background_tasks:
        from app.tasks.engine import run_engine_a
        background_tasks.add_task(run_engine_a.delay, property_id)
    return {"imported": count, "source": "customer_csv"}
