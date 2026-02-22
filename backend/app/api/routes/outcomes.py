"""Outcomes/actuals import for learning loop."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.market import Outcome
from app.services.org_access import user_has_property_access

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("/import")
async def import_outcomes(
    property_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import outcomes/actuals CSV for forecast error tracking and model calibration."""
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    import pandas as pd
    import io

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")

    header_norm = {str(h).strip().lower().replace(" ", "_"): h for h in df.columns}
    stay_col = header_norm.get("stay_date") or header_norm.get("staydate")
    adr_col = header_norm.get("adr") or header_norm.get("actual_adr")
    occ_col = header_norm.get("occupancy") or header_norm.get("actual_occupancy")
    rev_col = header_norm.get("revenue") or header_norm.get("actual_revenue")

    if not stay_col:
        raise HTTPException(status_code=400, detail="CSV must have stay_date column")

    count = 0
    for _, row in df.iterrows():
        stay_val = row.get(stay_col)
        if pd.isna(stay_val):
            continue
        try:
            stay_str = pd.to_datetime(stay_val).date().isoformat()
        except (ValueError, TypeError):
            continue
        adr = float(row[adr_col]) if adr_col and pd.notna(row.get(adr_col)) else None
        occ = float(row[occ_col]) if occ_col and pd.notna(row.get(occ_col)) else None
        rev = float(row[rev_col]) if rev_col and pd.notna(row.get(rev_col)) else None

        outcome = Outcome(
            property_id=property_id,
            stay_date=stay_str,
            actual_adr=adr,
            actual_occupancy=occ,
            actual_revenue=rev,
        )
        db.add(outcome)
        count += 1

    await db.flush()
    return {"imported": count}
