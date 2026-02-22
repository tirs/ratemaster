"""Billing - base fee + revenue share, invoice-ready output."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.engine import EngineRun, Recommendation
from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.services.org_access import get_org_ids_for_user, user_has_property_access

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/invoice")
async def get_invoice(
    property_id: str | None = None,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly invoice-ready output: base fee + revenue share + audit trail."""
    from datetime import date

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {
            "year": year,
            "month": month,
            "items": [],
            "total_base_fee": 0,
            "total_revenue_share": 0,
            "grand_total": 0,
        }
    props_query = select(Property).where(
        Property.organization_id.in_(org_ids)
    )
    if property_id:
        props_query = props_query.where(Property.id == property_id)
    result = await db.execute(props_query)
    props = result.scalars().all()

    items = []
    for prop in props:
        base_fee = float(prop.base_monthly_fee or 0)
        rev_share_pct = float(prop.revenue_share_pct or 0)

        lift_conditions = [
            EngineRun.property_id == prop.id,
            Recommendation.applied == True,
            Recommendation.stay_date >= start.isoformat(),
            Recommendation.stay_date < end.isoformat(),
        ]
        if prop.contract_effective_from:
            lift_conditions.append(
                Recommendation.stay_date >= prop.contract_effective_from.isoformat()
            )
        if prop.contract_effective_to:
            lift_conditions.append(
                Recommendation.stay_date <= prop.contract_effective_to.isoformat()
            )

        lift_query = (
            select(func.coalesce(func.sum(Recommendation.delta_dollars), 0))
            .join(EngineRun)
            .where(and_(*lift_conditions))
        )
        lift_result = await db.execute(lift_query)
        realized_lift = float(lift_result.scalar() or 0)

        flow_through = float(prop.flow_through_pct or 70) / 100
        gop_lift = realized_lift * flow_through

        rev_share_base = gop_lift if prop.revenue_share_on_gop else realized_lift
        rev_share_amount = rev_share_base * (rev_share_pct / 100)

        items.append({
            "property_id": prop.id,
            "property_name": prop.name,
            "base_fee": base_fee,
            "revenue_share_pct": rev_share_pct,
            "revenue_share_on_gop": prop.revenue_share_on_gop,
            "realized_lift": realized_lift,
            "gop_lift": gop_lift,
            "revenue_share_amount": rev_share_amount,
            "total": base_fee + rev_share_amount,
        })

    return {
        "year": year,
        "month": month,
        "items": items,
        "total_base_fee": sum(i["base_fee"] for i in items),
        "total_revenue_share": sum(i["revenue_share_amount"] for i in items),
        "grand_total": sum(i["total"] for i in items),
    }


@router.get("/yoy")
async def yoy_report(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Year-over-year reporting: applied recommendations + uploaded data (prior_year, current)."""
    if not await user_has_property_access(db, current_user.id, property_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Property not found")

    # 1. Applied recommendations YoY (from Engine A/B runs)
    year_expr = func.left(Recommendation.stay_date, 4)
    rec_result = await db.execute(
        select(
            year_expr.label("year"),
            func.sum(Recommendation.delta_dollars).label("total_lift"),
            func.count(Recommendation.id).label("applied_count"),
        )
        .select_from(Recommendation)
        .join(EngineRun, Recommendation.engine_run_id == EngineRun.id)
        .where(
            EngineRun.property_id == property_id,
            Recommendation.applied == True,
        )
        .group_by(year_expr)
    )
    rec_rows = rec_result.all()
    trends = [
        {"year": r.year, "total_lift": float(r.total_lift or 0), "applied_count": r.applied_count}
        for r in rec_rows
    ]

    # 2. Uploaded data YoY (from prior_year + current snapshots)
    year_expr_data = func.left(DataSnapshotRow.stay_date, 4)
    data_result = await db.execute(
        select(
            year_expr_data.label("year"),
            DataSnapshot.snapshot_type,
            func.coalesce(func.sum(DataSnapshotRow.revenue), 0).label("total_revenue"),
            func.count(DataSnapshotRow.id).label("row_count"),
        )
        .select_from(DataSnapshotRow)
        .join(DataSnapshot, DataSnapshotRow.snapshot_id == DataSnapshot.id)
        .where(DataSnapshot.property_id == property_id)
        .where(func.length(DataSnapshotRow.stay_date) >= 4)
        .group_by(year_expr_data, DataSnapshot.snapshot_type)
    )
    data_rows = data_result.all()
    data_trends = [
        {
            "year": r.year,
            "snapshot_type": r.snapshot_type,
            "total_revenue": float(r.total_revenue or 0),
            "row_count": r.row_count,
        }
        for r in data_rows
    ]

    # 3. Fallback: if no grouped data but snapshots exist, show snapshot summary
    if not data_trends:
        snap_result = await db.execute(
            select(DataSnapshot.snapshot_type, DataSnapshot.row_count)
            .where(DataSnapshot.property_id == property_id)
        )
        for r in snap_result.all():
            data_trends.append({
                "year": "—",
                "snapshot_type": r.snapshot_type,
                "total_revenue": 0,
                "row_count": r.row_count or 0,
            })

    return {
        "property_id": property_id,
        "trends": trends,
        "data_trends": data_trends,
    }
