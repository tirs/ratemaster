"""Data import API routes."""
import json
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, status, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.schemas.data_import import DataSnapshotResponse
from app.services.data_import import parse_csv, compute_data_health, detect_column_mapping

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Preview CSV headers for column mapping. Returns headers and auto-detected mapping."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file required",
        )
    content = await file.read()
    try:
        import pandas as pd
        import io
        df = pd.read_csv(io.BytesIO(content), nrows=0)
        headers = list(df.columns)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")
    detected = detect_column_mapping(content)
    return {
        "headers": headers,
        "detected_mapping": detected,
        "logical_fields": [
            "stay_date", "rooms_available", "total_rooms", "rooms_sold",
            "adr", "total_rate", "revenue", "booking_date",
        ],
    }


@router.post("/import", response_model=DataSnapshotResponse)
async def import_csv(
    background_tasks: BackgroundTasks,
    property_id: str = Form(...),
    snapshot_type: str = Form("current"),
    file: UploadFile = File(...),
    column_mapping: str = Form(""),
    snapshot_date: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSnapshotResponse:
    """Upload CSV with column mapping. Creates snapshot + rows."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file required",
        )

    # Verify property access
    result = await db.execute(
        select(Property)
        .join(Organization)
        .where(
            Property.id == property_id,
            Organization.owner_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    content = await file.read()
    if column_mapping:
        try:
            mapping = json.loads(column_mapping)
            if not isinstance(mapping, dict):
                mapping = {}
        except json.JSONDecodeError:
            mapping = {}
    else:
        mapping = {}
    if not mapping:
        mapping = detect_column_mapping(content)
    if "stay_date" not in mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not detect stay_date column. Provide column_mapping or use CSV with date/stay_date column.",
        )
    rows, errors = parse_csv(content, mapping)

    health, recommended_fixes = compute_data_health(rows, errors)

    snap_date = snapshot_date.strip() or None
    if not snap_date and rows:
        dates = [r.get("stay_date") for r in rows if r.get("stay_date")]
        if dates:
            snap_date = min(dates)

    snapshot = DataSnapshot(
        property_id=property_id,
        snapshot_type=snapshot_type,
        snapshot_date=snap_date,
        column_mapping=mapping,
        row_count=len(rows),
        validation_errors={"errors": errors, "recommended_fixes": recommended_fixes} if (errors or recommended_fixes) else None,
        data_health_score=health,
    )
    db.add(snapshot)
    await db.flush()

    for r in rows[:5000]:  # Limit for initial implementation
        raw = dict(r.get("raw_data", {}))
        if r.get("booking_date"):
            raw["booking_date"] = r["booking_date"]
        row_obj = DataSnapshotRow(
            snapshot_id=snapshot.id,
            stay_date=r.get("stay_date", ""),
            rooms_available=r.get("rooms_available"),
            total_rooms=r.get("total_rooms"),
            rooms_sold=r.get("rooms_sold"),
            adr=r.get("adr"),
            total_rate=r.get("total_rate"),
            revenue=r.get("revenue"),
            raw_data=raw,
        )
        db.add(row_obj)

    if snapshot_type == "prior_year" and background_tasks:
        from app.tasks.ingestion import compute_yoy_curves_task
        background_tasks.add_task(compute_yoy_curves_task.delay, property_id)

    return DataSnapshotResponse(
        id=snapshot.id,
        property_id=snapshot.property_id,
        snapshot_date=snapshot.snapshot_date,
        snapshot_type=snapshot.snapshot_type,
        row_count=snapshot.row_count,
        data_health_score=snapshot.data_health_score,
        created_at=snapshot.created_at.isoformat(),
        recommended_fixes=recommended_fixes,
    )


@router.get("/snapshots", response_model=list[DataSnapshotResponse])
async def list_snapshots(
    property_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DataSnapshotResponse]:
    """List data snapshots for user's properties."""
    from app.services.org_access import get_org_ids_for_user

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = (
        select(DataSnapshot)
        .join(Property)
        .where(Property.organization_id.in_(org_ids))
    )
    if property_id:
        query = query.where(DataSnapshot.property_id == property_id)
    query = query.order_by(DataSnapshot.created_at.desc())
    result = await db.execute(query)
    snapshots = result.scalars().all()
    return [
        DataSnapshotResponse(
            id=s.id,
            property_id=s.property_id,
            snapshot_date=s.snapshot_date,
            snapshot_type=s.snapshot_type,
            row_count=s.row_count,
            data_health_score=s.data_health_score,
            created_at=s.created_at.isoformat(),
            recommended_fixes=s.validation_errors.get("recommended_fixes", []) if s.validation_errors else None,
        )
        for s in snapshots
    ]


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a data snapshot and its rows. User must have access to the property."""
    from app.services.org_access import get_org_ids_for_user

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found or access denied",
        )
    result = await db.execute(
        select(DataSnapshot)
        .join(Property)
        .where(
            DataSnapshot.id == snapshot_id,
            Property.organization_id.in_(org_ids),
        )
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found or access denied",
        )
    await db.execute(delete(DataSnapshotRow).where(DataSnapshotRow.snapshot_id == snapshot_id))
    await db.execute(delete(DataSnapshot).where(DataSnapshot.id == snapshot_id))


@router.get("/health-summary")
async def health_summary(
    property_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Data health rollup across properties, or per-property when property_id given."""
    from sqlalchemy import func

    from app.services.org_access import get_org_ids_for_user, user_has_property_access

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {"properties_with_data": 0, "average_health_score": None, "property_health": None}
    if property_id:
        if not await user_has_property_access(db, current_user.id, property_id):
            return {"properties_with_data": 0, "average_health_score": None, "property_health": None}
        result = await db.execute(
            select(func.max(DataSnapshot.data_health_score))
            .join(Property)
            .where(
                DataSnapshot.property_id == property_id,
                Property.organization_id.in_(org_ids),
            )
        )
        score = result.scalar()
        return {
            "properties_with_data": 1 if score else 0,
            "average_health_score": float(score) if score else None,
            "property_health": float(score) if score else None,
        }
    subq = (
        select(
            DataSnapshot.property_id,
            func.max(DataSnapshot.data_health_score).label("max_health"),
        )
        .join(Property)
        .where(Property.organization_id.in_(org_ids))
        .group_by(DataSnapshot.property_id)
    )
    result = await db.execute(subq)
    rows = result.all()
    properties_with_data = len(rows)
    avg_health = (
        sum(r.max_health or 0 for r in rows) / properties_with_data
        if properties_with_data
        else None
    )
    return {
        "properties_with_data": properties_with_data,
        "average_health_score": round(avg_health, 1) if avg_health is not None else None,
        "property_health": None,
    }
