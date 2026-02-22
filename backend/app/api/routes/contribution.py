"""Contribution and value attribution API."""
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.engine import EngineRun, Recommendation
from app.models.market import Outcome
from app.services.org_access import get_org_ids_for_user

router = APIRouter(prefix="/contribution", tags=["contribution"])


@router.get("/summary")
async def contribution_summary(
    property_id: str | None = None,
    horizon_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Projected incremental revenue vs baseline.
    Realized: from applied recommendations, or from imported actuals when available.
    """
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {
            "projected_lift_30d": 0,
            "projected_lift_60d": 0,
            "projected_lift_90d": 0,
            "realized_lift_mtd": 0,
            "realized_from_actuals": False,
            "recommendations_in_horizon": 0,
            "applied_count": 0,
            "estimated_gop_lift": 0,
            "flow_through_pct": 70,
        }
    props_query = select(Property).where(Property.organization_id.in_(org_ids))
    if property_id:
        props_query = props_query.where(Property.id == property_id)
    props_result = await db.execute(props_query)
    props = props_result.scalars().all()
    prop_ids = [p.id for p in props]
    if not prop_ids:
        return {
            "projected_lift_30d": 0,
            "projected_lift_60d": 0,
            "projected_lift_90d": 0,
            "realized_lift_mtd": 0,
            "realized_from_actuals": False,
            "recommendations_in_horizon": 0,
            "applied_count": 0,
            "estimated_gop_lift": 0,
            "flow_through_pct": 70,
        }

    rec_query = (
        select(
            Recommendation.stay_date,
            Recommendation.delta_dollars,
            Recommendation.current_bar,
            Recommendation.applied,
            EngineRun.property_id,
        )
        .join(EngineRun)
        .where(EngineRun.property_id.in_(prop_ids))
    )
    result = await db.execute(rec_query)
    rows = result.all()

    today = date.today()
    horizons = [(30, today + timedelta(days=30)), (60, today + timedelta(days=60)), (90, today + timedelta(days=90))]
    projected = {30: Decimal("0"), 60: Decimal("0"), 90: Decimal("0")}
    realized_lift = Decimal("0")
    applied_count = 0
    total_count = 0

    for r in rows:
        try:
            stay_d = date.fromisoformat(r.stay_date)
        except (ValueError, TypeError):
            continue
        if stay_d < today:
            continue
        delta = r.delta_dollars or Decimal("0")
        if stay_d <= today + timedelta(days=30):
            total_count += 1
            if r.applied:
                applied_count += 1
                realized_lift += delta
        for days, end_dt in horizons:
            if stay_d <= end_dt:
                projected[days] += delta

    realized_from_actuals = False
    outcome_result = await db.execute(
        select(Outcome)
        .where(Outcome.property_id.in_(prop_ids))
        .where(Outcome.stay_date >= today.isoformat())
        .where(Outcome.stay_date <= (today + timedelta(days=horizon_days)).isoformat())
        .where(Outcome.recommendation_id.isnot(None))
        .where(Outcome.actual_revenue.isnot(None))
    )
    outcomes = outcome_result.scalars().all()
    if outcomes:
        rec_ids = [o.recommendation_id for o in outcomes if o.recommendation_id]
        rec_result = await db.execute(
            select(Recommendation.id, Recommendation.stay_date, Recommendation.current_bar)
            .where(Recommendation.id.in_(rec_ids))
        )
        rec_map = {r.id: r for r in rec_result.all()}
        actuals_lift = Decimal("0")
        for o in outcomes:
            rec = rec_map.get(o.recommendation_id) if o.recommendation_id else None
            if not rec or not rec.current_bar or not o.actual_adr or not o.actual_revenue:
                continue
            try:
                stay_d = date.fromisoformat(o.stay_date)
            except (ValueError, TypeError):
                continue
            if stay_d < today or stay_d > today + timedelta(days=horizon_days):
                continue
            baseline_rev = float(rec.current_bar) * float(o.actual_revenue) / float(o.actual_adr)
            actuals_lift += Decimal(str(float(o.actual_revenue) - baseline_rev))
        if outcomes:
            realized_lift = actuals_lift
            realized_from_actuals = True

    flow_through = 0.7
    flow_through_pct = 70
    if property_id:
        prop = next((p for p in props if p.id == property_id), None)
        if prop and prop.flow_through_pct:
            flow_through = float(prop.flow_through_pct) / 100
            flow_through_pct = int(prop.flow_through_pct)
    else:
        # All properties: use weighted avg or default
        total_ft = sum(float(p.flow_through_pct or 70) for p in props)
        flow_through_pct = int(round(total_ft / len(props))) if props else 70
        flow_through = flow_through_pct / 100

    return {
        "projected_lift_30d": float(projected[30]),
        "projected_lift_60d": float(projected[60]),
        "projected_lift_90d": float(projected[90]),
        "realized_lift_mtd": float(realized_lift),
        "realized_from_actuals": realized_from_actuals,
        "recommendations_in_horizon": total_count,
        "applied_count": applied_count,
        "estimated_gop_lift": float(projected[30]) * flow_through,
        "flow_through_pct": flow_through_pct,
    }


@router.get("/top-wins")
async def top_wins(
    property_id: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top opportunities by delta."""
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = (
        select(Recommendation)
        .join(EngineRun)
        .join(Property)
        .where(
            Property.organization_id.in_(org_ids),
            Recommendation.delta_dollars > 0,
        )
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)
    query = query.order_by(Recommendation.delta_dollars.desc()).limit(limit)

    result = await db.execute(query)
    recs = result.scalars().all()
    return [
        {
            "stay_date": r.stay_date,
            "delta_dollars": float(r.delta_dollars or 0),
            "suggested_bar": float(r.suggested_bar or 0),
            "applied": r.applied,
        }
        for r in recs
    ]


@router.get("/avoided-losses")
async def avoided_losses(
    property_id: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recommendations we did NOT apply that would have lowered revenue.
    Avoided losses = delta_dollars < 0, applied = false.
    """
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = (
        select(Recommendation)
        .join(EngineRun)
        .join(Property)
        .where(
            Property.organization_id.in_(org_ids),
            Recommendation.delta_dollars < 0,
            Recommendation.applied == False,
        )
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)
    query = query.order_by(Recommendation.delta_dollars.asc()).limit(limit)

    result = await db.execute(query)
    recs = result.scalars().all()
    return [
        {
            "stay_date": r.stay_date,
            "delta_dollars": float(r.delta_dollars or 0),
            "suggested_bar": float(r.suggested_bar or 0),
            "current_bar": float(r.current_bar or 0),
        }
        for r in recs
    ]
